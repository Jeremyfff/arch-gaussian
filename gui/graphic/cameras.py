import logging
import math

import numpy
import numpy as np
import torch
from moderngl_window.opengl.projection import Projection3D
from pyrr import Matrix44, Vector3, vector, vector3

from gui.utils.transform_utils import world_matrix, gl_up

torch.set_printoptions(precision=3, sci_mode=False)

# Direction Definitions
RIGHT = 1
LEFT = 2
FORWARD = 3
BACKWARD = 4
UP = 5
DOWN = 6

# Movement Definitions
STILL = 0
POSITIVE = 1
NEGATIVE = 2


class GL_3DGS_Camera:
    """同时支持Opengl和3dgs渲染的camera"""

    def __init__(self, width, height):
        # 1. values for orbit camera
        # 2 和 3 中的数值由这里的值驱动
        self._radius = 5.0  # radius in base units
        self._angle_x, self._angle_y = -45.0, -60.0  # angles in degrees
        self._target = Vector3((0.0, 0.0, 0.0), dtype="f4")  # camera target in base units
        self._mouse_sensitivity = 1.0
        self._zoom_sensitivity = 1.0

        # 2. init values for camera
        self._position = Vector3([0.0, 0.0, 0.0], dtype="f4")
        self._front = Vector3([0.0, 0.0, 1.0], dtype="f4")
        self._up = Vector3([0.0, 1.0, 0.0], dtype="f4")
        self._right = Vector3([1.0, 0.0, 0.0], dtype="f4")

        self._projection = Projection3D(1.0, 60.0, 0.1, 1000.0)
        self._matrix = Matrix44.identity(dtype="f4")

        # 3. values for gaussian camera
        import torch
        from utils.graphics_utils import pa2tr, getWorld2View2, tr2pa, getProjectionMatrix
        self.torch = torch
        self.pa2tr, self.tr2pa, self.getWorld2View2, self.getProjectionMatrix = pa2tr, tr2pa, getWorld2View2, getProjectionMatrix

        self._image_width = width
        self._image_height = height

        self._GAUSSIAN_WORLD_MATRIX = self.torch.tensor(world_matrix).cuda()
        self._TRANS = np.array([0.0, 0.0, 0.0])
        self._SCALE = 1.0

        self._u = None  # up, right, front in gaussian space
        self._r = None
        self._f = None
        self._P = None
        self._A = None
        self._R = None
        self._T = None

        self._world_to_view_matrix = None
        self._world_view_transform = None
        self._projection_matrix = None
        self._full_proj_transform = None
        self._camera_center = None

    # region 直接驱动的变量或方法
    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = value

    @property
    def angle_x(self) -> float:
        return self._angle_x

    @angle_x.setter
    def angle_x(self, value: float):
        self._angle_x = value

    @property
    def angle_y(self) -> float:
        return self._angle_y

    @angle_y.setter
    def angle_y(self, value: float):
        self._angle_y = value

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    @property
    def mouse_sensitivity(self) -> float:
        return self._mouse_sensitivity

    @mouse_sensitivity.setter
    def mouse_sensitivity(self, value: float):
        self._mouse_sensitivity = value

    @property
    def zoom_sensitivity(self) -> float:
        return self._zoom_sensitivity

    @zoom_sensitivity.setter
    def zoom_sensitivity(self, value: float):
        self._zoom_sensitivity = value

    def rot_state(self, dx: float, dy: float) -> None:
        self.angle_x += dx * self.mouse_sensitivity / 10.0
        self.angle_y += dy * self.mouse_sensitivity / 10.0

        # clamp the y angle to avoid weird rotations
        self.angle_y = max(min(self.angle_y, -5.0), -175.0)

    def zoom_state(self, y_offset: float) -> None:
        # allow zooming in/out
        self.radius -= y_offset * self._zoom_sensitivity
        self.radius = max(1.0, self.radius)

    # endregion

    # region 被动驱动的变量
    def update(self):
        """calculate camera parameters by camera angle_x, angle_y radius"""
        position = (
            math.cos(math.radians(self.angle_x)) * math.sin(math.radians(self.angle_y)) * self.radius + self.target[0],
            math.cos(math.radians(self.angle_y)) * self.radius + self.target[1],
            math.sin(math.radians(self.angle_x)) * math.sin(math.radians(self.angle_y)) * self.radius + self.target[2],
        )
        self._position = Vector3(position, dtype="f4")

        self._front = vector.normalise(self._target - self._position)
        self._right = vector.normalise(vector3.cross(self._front, gl_up))
        self._up = vector.normalise(vector3.cross(self._right, self._front))

        self._matrix = Matrix44.look_at(
            self._position,
            self._target,
            self._up,
            dtype="f4",
        )

        self._f = vector.normalise(self._target - self._position)
        self._r = vector.normalise(vector3.cross(self._front, -gl_up))
        self._u = vector.normalise(vector3.cross(self.r, self._front))

        self._A = np.array([self.r, self.u, self.f])
        self._P = np.array(position)

        self._T, self._R = self.pa2tr(self._P, self._A)

        self._world_to_view_matrix = torch.tensor(self.getWorld2View2(self._R, self._T, self._TRANS, self._SCALE), device="cuda")
        self._world_view_transform = self._world_to_view_matrix.transpose(0, 1)
        self._world_view_transform = self._GAUSSIAN_WORLD_MATRIX @ self._world_view_transform
        self._projection_matrix = self.torch.tensor(self._projection.matrix, device="cuda")
        self._full_proj_transform = self._world_view_transform @ self._projection_matrix
        self._camera_center = self._world_view_transform.inverse()[3, :3]



    def update_use_TR(self, T, R):
        """give a specific T and R matrix to move the camera"""
        self._T = T
        self._R = R
        self._P, self._A = self.tr2pa(self._T, self._R)
        self._position = Vector3(self._P, dtype="f4")
        self._right = Vector3(self._A[0], dtype="f4")
        self._up = Vector3(self._A[1], dtype="f4")
        self._front = Vector3(self._A[2], dtype="f4")

        self._matrix = Matrix44.look_at(
            self._position,
            self._target,
            self._up,
            dtype="f4",
        )

        self._world_view_transform = self.torch.tensor(self.getWorld2View2(self._R, self._T, self._TRANS, self._SCALE), device="cuda").transpose(0, 1)
        self._projection_matrix = self.getProjectionMatrix(znear=self.projection.near, zfar=self.projection.far, fovX=self.FoVx, fovY=self.FoVy).transpose(0, 1).cuda()
        self._full_proj_transform = self._world_view_transform @ self._projection_matrix
        self._camera_center = self._world_view_transform.inverse()[3, :3]

    def update_size(self, width, height):
        logging.info(f'gaussian camera size updated to w: {width} h: {height} ')
        self._image_width = width
        self._image_height = height
        self._projection.update(aspect_ratio=(float(width) / float(height)))

    @property
    def projection(self):
        return self._projection

    @property
    def position(self):
        return self._position

    @property
    def up(self):
        return self._up

    @property
    def front(self):
        return self._front

    @property
    def right(self):
        return self._right

    @property
    def matrix(self) -> numpy.ndarray:
        return self._matrix

    @property
    def FoVy(self):
        return math.radians(self.projection.fov)

    @property
    def FoVx(self):
        return math.radians(self.projection.fov * self.projection.aspect_ratio)

    @property
    def image_height(self):
        return self._image_height

    @property
    def image_width(self):
        return self._image_width

    @property
    def world_view_transform(self):
        return self._world_view_transform

    @property
    def projection_matrix(self):
        return self._projection_matrix

    @property
    def full_proj_transform(self):
        return self._full_proj_transform

    @property
    def camera_center(self):
        return self._camera_center

    @property
    def P(self):
        return self._P

    @property
    def A(self):
        return self._A

    @property
    def f(self):
        return self._f

    @property
    def r(self):
        return self._r

    @property
    def u(self):
        return self._u

    # endregion
