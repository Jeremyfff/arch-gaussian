import logging
import math
from abc import abstractmethod
from typing import Optional

import imgui
import moderngl
import numpy as np
from moderngl_window import geometry
from moderngl_window.opengl.vao import VAO
from moderngl_window.scene.camera import Camera
from pyrr import Matrix44

from gui import components as c
from gui import global_var as g


class BaseGeometry:
    @abstractmethod
    def __init__(self, name):
        self.name = name
        self.active = True

    @abstractmethod
    def render(self, camera: Camera):
        pass

    @abstractmethod
    def operation_panel(self):
        pass


class BaseGeometry3D(BaseGeometry):
    """auto update m_proj m_model m_camera"""

    def __init__(self, name, program_path, vao: Optional[VAO] = None, mode=moderngl.TRIANGLES):
        super().__init__(name)
        if vao is None:
            self.vao: VAO = VAO(name, mode=mode)
        else:
            self.vao: VAO = vao
        self.prog = g.mWindowEvent.load_program(program_path)
        self.ctx = g.mWindowEvent.ctx
        self.vertices = -1
        self.first = 0
        self.instances = 1

        self.rotation = (0, 0, 0)
        self.translation = (0, 0, 0)

        self.world_matrix = Matrix44.from_eulers((-math.pi / 2, 0, 0), dtype='f4')

    def before_render(self):
        pass

    def render(self, camera: Camera):
        rotation = Matrix44.from_eulers(self.rotation, dtype='f4')
        translation = Matrix44.from_translation(self.translation, dtype='f4')
        model_view = self.world_matrix * translation * rotation
        # model_view = translation * rotation
        self.prog['m_proj'].write(camera.projection.matrix)
        self.prog['m_model'].write(model_view)
        self.prog['m_camera'].write(camera.matrix)
        self.before_render()
        self.vao.render(self.prog, vertices=self.vertices, first=self.first, instances=self.instances)
        self.after_render()

    def after_render(self):
        pass

    @abstractmethod
    def operation_panel(self):
        pass


class PointCloud(BaseGeometry3D):
    def __init__(self, name, pos_arr, color_arr):
        """color_arr should be in range(0, 1)"""
        if color_arr.shape[1] == 3:
            super().__init__(name, program_path='programs/point_cloud_rgb.glsl', mode=moderngl.POINTS)
            self.vao.buffer(pos_arr, '3f', ['in_position'])
            self.vao.buffer(color_arr, '3f', ['in_color'])

        else:
            super().__init__(name, program_path='programs/point_cloud_rgba.glsl', mode=moderngl.POINTS)
            self.vao.buffer(pos_arr, '3f', ['in_position'])
            self.vao.buffer(color_arr, '4f', ['in_color'])

    @abstractmethod
    def operation_panel(self):
        pass


class Line3D(BaseGeometry3D):
    def __init__(self, points, color=(1, 1, 1, 1)):
        pos_arr = np.array(points, dtype=np.float32)
        if len(color) == 3:
            super().__init__('line_3d', program_path='programs/line_rgb.glsl', mode=moderngl.LINES)
        else:
            super().__init__('line_3d', program_path='programs/line_rgba.glsl', mode=moderngl.LINES)
        self.vao.buffer(pos_arr, '3f', ['in_position'])
        self.prog['color'].value = color

    @abstractmethod
    def operation_panel(self):
        pass


class Axis3D(BaseGeometry):
    def __init__(self, name='axis3d'):
        super().__init__(name)
        self.axis_x = Line3D(points=((0, 0, 0), (100, 0, 0)), color=(1, 0, 0, 1))
        self.axis_y = Line3D(points=((0, 0, 0), (0, 100, 0)), color=(0, 1, 0, 1))
        self.axis_z = Line3D(points=((0, 0, 0), (0, 0, 100)), color=(0, 0, 1, 1))

    def render(self, camera: Camera):
        self.axis_x.render(camera)
        self.axis_y.render(camera)
        self.axis_z.render(camera)

    @abstractmethod
    def operation_panel(self):
        pass


class SimpleCube(BaseGeometry3D):
    def __init__(self, name, size=(1, 1, 1), color=(1.0, 1.0, 1.0, 1.0)):
        super().__init__(name, program_path='programs/cube_simple.glsl', vao=geometry.cube(size))
        self.prog['color'].value = color

    @abstractmethod
    def operation_panel(self):
        pass


class CubeInstance(BaseGeometry3D):
    def __init__(self):
        super().__init__('cube_instance', program_path='programs/cube_simple_instanced.glsl',
                         vao=geometry.cube(size=(2, 2, 2)))
        # Generate per instance data representing a grid of cubes
        N = 100
        self.instances = N * N

        def gen_data(x_res, z_res, spacing=2.5):
            """Generates a grid of N * N positions and random colors on the xz plane"""
            for y in range(z_res):
                for x in range(x_res):
                    yield -N * spacing / 2 + spacing * x
                    yield 0
                    yield -N * spacing / 2 + spacing * y
                    yield np.random.uniform(0, 1)
                    yield np.random.uniform(0, 1)
                    yield np.random.uniform(0, 1)

        self.instance_data = self.ctx.buffer(np.fromiter(gen_data(N, N), 'f4', count=self.instances * 6))
        self.vao.buffer(self.instance_data, '3f 3f/i', ['in_offset', 'in_color'])

    def before_render(self):
        self.prog['time'].value = g.mTime

    @abstractmethod
    def operation_panel(self):
        pass


class QuadFullScreen(BaseGeometry):
    def __init__(self, name, program_path):
        super().__init__(name)

        self.vao: VAO = geometry.quad_fs()
        self.prog = g.mWindowEvent.load_program(program_path)
        self.ctx = g.mWindowEvent.ctx

    def render(self, camera: None):
        _ = camera
        self.vao.render(self.prog)

    @abstractmethod
    def operation_panel(self):
        pass


class GaussianPointCloud(BaseGeometry):
    """包裹了一个PointCloud的geometry"""

    def __init__(self, name):
        super().__init__(name)
        from src.manager.gaussian_manager import GaussianManager

        self.gm: Optional[GaussianManager] = None
        self.gaussian_point_cloud: Optional[PointCloud] = None
        self.gaussian_size_threshold = 0.001

    def set_gaussian_manager(self, gaussian_manager):
        self.gm = gaussian_manager

    def update_gaussian_points(self):
        if self.gm is None:
            logging.warning('no gaussian manger')
            return
        logging.info(f'updating gaussian points')
        pos_arr = self.gm.gaussians.get_xyz.detach().cpu().numpy()  # (n, 3)
        rgb_arr = self.gm.gaussians.get_features_dc.detach().cpu().numpy().squeeze(axis=1)  # (n, 3)
        alpha_arr = self.gm.gaussians.get_alpha.detach().cpu().numpy().squeeze(axis=1)
        size_arr = self.gm.gaussians.get_scaling.detach().cpu().numpy()
        print(f'before: {len(pos_arr)}')
        non_zero_mask = np.all(size_arr > self.gaussian_size_threshold, axis=1)
        pos_arr = pos_arr[non_zero_mask]
        rgb_arr = rgb_arr[non_zero_mask]
        alpha_arr = alpha_arr[non_zero_mask]
        print(f'after: {len(pos_arr)}')
        rgba = np.hstack((rgb_arr, alpha_arr.reshape(-1, 1)))
        SH_C0 = 0.28209479177387814
        rgba[:, 0:3] = (0.5 + SH_C0 * rgba[:, 0:3])
        rgba[:, 3] = (1 / (1 + np.exp(-rgba[:, 3])))
        rgba = np.clip(rgba, 0.0, 1.0)
        self.gaussian_point_cloud = PointCloud(f'{self.name}_point_cloud', pos_arr, rgba)

    def show_debug_info(self):
        c.bold_text(f'[{self.__class__.__name__}(class)]')

    @abstractmethod
    def operation_panel(self):
        if imgui.button('update gaussian points'):
            self.update_gaussian_points()
        _, self.gaussian_size_threshold = imgui.slider_float('size_threshold', self.gaussian_size_threshold, 0.0, 0.1)

    def render(self, camera: Camera):
        self.gaussian_point_cloud.render(camera)
