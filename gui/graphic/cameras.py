import math

import numpy as np
import torch
from moderngl_window.scene.camera import OrbitCamera
from pyrr import Matrix44

torch.set_printoptions(precision=3, sci_mode=False)


class OrbitGaussianCamera(OrbitCamera):
    def __init__(self, width, height):
        super().__init__()
        self._image_width = width
        self._image_height = height
        import torch
        self.torch = torch
        from utils.graphics_utils import pa2tr, getWorld2View2, tr2pa, getProjectionMatrix
        self.pa2tr = pa2tr
        self.tr2pa = tr2pa
        self.getWorld2View2 = getWorld2View2
        self.getProjectionMatrix = getProjectionMatrix

        self._WORLD_UP = np.array([0, -1, 0])
        self._WORLD_MATRIX = self.torch.tensor(Matrix44.from_eulers((-math.pi / 2, 0, 0), dtype='f4')).cuda()
        self._TRANS = np.array([0.0, 0.0, 0.0])
        self._SCALE = 1.0
        self._r = None
        self._u = None
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

    def update_use_TR(self, T, R):
        """give a specific T and R matrix to move the camera"""
        self._T = T
        self._R = R
        self._world_view_transform = self.torch.tensor(
            self.getWorld2View2(self._R, self._T, self._TRANS, self._SCALE)
        ).transpose(0, 1).cuda()
        self._projection_matrix = self.getProjectionMatrix(znear=self.projection.near, zfar=self.projection.far,
                                                           fovX=self.FoVx, fovY=self.FoVy).transpose(0, 1).cuda()
        self._full_proj_transform = self._world_view_transform @ self._projection_matrix
        self._camera_center = self._world_view_transform.inverse()[3, :3]

    def update_size(self, width, height):
        print(f'gaussian camera size updated to w: {width} h: {height} ')
        self._image_width = width
        self._image_height = height

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

    def update(self):
        """calculate camera parameters by camera angle_x, angle_y radius"""
        position = np.array((
            math.cos(math.radians(self.angle_x)) * math.sin(math.radians(self.angle_y)) * self.radius + self.target[0],
            math.cos(math.radians(self.angle_y)) * self.radius + self.target[1],
            math.sin(math.radians(self.angle_x)) * math.sin(math.radians(self.angle_y)) * self.radius + self.target[2],
        ))
        target = np.array(self.target)
        # 计算摄像机的前向向量
        self._f = target - position
        self._f = self._f / np.linalg.norm(self._f)

        # 计算向右向量
        self._r = np.cross(self._f, self._WORLD_UP)
        self._r = self._r / np.linalg.norm(self._r)

        # 计算向上向量
        self._u = np.cross(self._r, self._f)
        self._A = np.array([self._r, self._u, self._f])
        self._P = position

        self._T, self._R = self.pa2tr(self._P, self._A)

        self._world_to_view_matrix = torch.tensor(
            self.getWorld2View2(self._R, self._T, self._TRANS, self._SCALE)).cuda()
        self._world_view_transform = self._world_to_view_matrix.transpose(0, 1)
        self._world_view_transform = self._WORLD_MATRIX @ self._world_view_transform
        self._projection_matrix = self.torch.tensor(self.projection.matrix).cuda()
        self._full_proj_transform = self._world_view_transform @ self._projection_matrix
        self._camera_center = self._world_view_transform.inverse()[3, :3]

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
    def WORLD_MATRIX(self):
        return self._WORLD_MATRIX.cpu().numpy()
