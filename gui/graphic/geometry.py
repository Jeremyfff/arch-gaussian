import math
from abc import abstractmethod
from typing import Optional

import moderngl
import numpy as np
from moderngl_window import geometry
from moderngl_window.opengl.vao import VAO
from moderngl_window.scene.camera import Camera
from pyrr import Matrix44

from gui import global_var as g


class RenderableObject:
    @abstractmethod
    def render(self, camera: Camera):
        pass


class BaseGeometry3D(RenderableObject):
    """auto update m_proj m_model m_camera"""

    def __init__(self, name, program_path, vao: Optional[VAO] = None, mode=moderngl.TRIANGLES):
        self.name = name
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
        self.prog['m_proj'].write(camera.projection.matrix)
        self.prog['m_model'].write(model_view)
        self.prog['m_camera'].write(camera.matrix)
        self.before_render()
        self.vao.render(self.prog, vertices=self.vertices, first=self.first, instances=self.instances)
        self.after_render()

    def after_render(self):
        pass


class PointCloud(BaseGeometry3D):
    def __init__(self, pos_arr, color_arr):
        if color_arr.shape[1] == 3:
            super().__init__('point_cloud', program_path='programs/point_cloud_rgb.glsl', mode=moderngl.POINTS)
            self.vao.buffer(pos_arr, '3f', ['in_position'])
            self.vao.buffer(color_arr, '3f', ['in_color'])

        else:
            super().__init__('point_cloud', program_path='programs/point_cloud_rgba.glsl', mode=moderngl.POINTS)
            self.vao.buffer(pos_arr, '3f', ['in_position'])
            self.vao.buffer(color_arr, '4f', ['in_color'])


class Line3D(BaseGeometry3D):
    def __init__(self, points, color=(1, 1, 1, 1)):
        pos_arr = np.array(points, dtype=np.float32)
        if len(color) == 3:
            super().__init__('line_3d', program_path='programs/line_rgb.glsl', mode=moderngl.LINES)
        else:
            super().__init__('line_3d', program_path='programs/line_rgba.glsl', mode=moderngl.LINES)
        self.vao.buffer(pos_arr, '3f', ['in_position'])
        self.prog['color'].value = color


class Axis3D(RenderableObject):
    def __init__(self):
        self.axis_x = Line3D(points=((0, 0, 0), (100, 0, 0)), color=(1, 0, 0, 1))
        self.axis_y = Line3D(points=((0, 0, 0), (0, 100, 0)), color=(0, 1, 0, 1))
        self.axis_z = Line3D(points=((0, 0, 0), (0, 0, 100)), color=(0, 0, 1, 1))

    def render(self, camera: Camera):
        self.axis_x.render(camera)
        self.axis_y.render(camera)
        self.axis_z.render(camera)


class SimpleCube(BaseGeometry3D):
    def __init__(self, size=(1, 1, 1), color=(1.0, 1.0, 1.0, 1.0)):
        super().__init__('cube', program_path='programs/cube_simple.glsl', vao=geometry.cube(size))
        self.prog['color'].value = color


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
