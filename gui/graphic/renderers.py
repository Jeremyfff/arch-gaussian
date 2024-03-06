import imgui
import moderngl
import numpy as np

from gui import global_var as g
from gui import components as c
from gui.graphic import geometry
from gui.modules.graphic_module import CameraFrameBuffer


class CubeSimple(CameraFrameBuffer):

    def __init__(self, name, width, height, channel=4, camera_type='orbit'):
        super().__init__(name, width, height, channel, camera_type)

        self.cube = geometry.SimpleCube(size=(2, 2, 2))

    def render(self, **kwargs):
        self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST)
        self.fbo.use()
        self.fbo.clear(0, 0, 0, 0)

        self.cube.rotation = (g.mTime, g.mTime, g.mTime)
        self.cube.translation = (0.0, 0.0, -3.5)
        self.cube.render(self.camera)

    def show_debug_info(self):
        super().show_debug_info()


class CubeSimpleInstanced(CameraFrameBuffer):
    def __init__(self, name, width, height, channel=4, camera_type='orbit'):
        super().__init__(name, width, height, channel, camera_type)
        self.cubes = geometry.CubeInstance()

    def render(self, **kwargs):
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        self.fbo.use()
        self.fbo.clear()

        self.cubes.render(self.camera)

    def show_debug_info(self):
        super().show_debug_info()


class SceneInfoRenderer(CameraFrameBuffer):

    def __init__(self, name, width, height, channel=4, camera_type='orbit'):
        super().__init__(name, width, height, channel, camera_type)

        num = 100
        pos_arr = np.random.rand(num, 3).astype(np.float32)
        color_arr = np.random.rand(num, 4).astype(np.float32)
        self.point_cloud = geometry.PointCloud(pos_arr, color_arr)
        self.cube = geometry.SimpleCube()
        self.axis = geometry.Axis3D()
        self.custom_line = geometry.Line3D(points=(
            (0, 0, 0),
            (1, 1, 1),
            (3, 3, 3),
            (2, 1, 0)
        ))

        self._debug_num_points = len(pos_arr)

    def update_buffer(self, pos_arr, color_arr):
        pos_arr = pos_arr.astype(np.float32)
        color_arr = color_arr.astype(np.float32)
        self.point_cloud = geometry.PointCloud(pos_arr, color_arr)

        self._debug_num_points = len(pos_arr)

    def render(self, **kwargs):
        self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST | moderngl.PROGRAM_POINT_SIZE)
        self.ctx.point_size = 10
        self.fbo.use()
        self.fbo.clear()
        self.cube.render(self.camera)
        self.axis.render(self.camera)
        self.custom_line.render(self.camera)
        self.point_cloud.render(self.camera)

    def show_debug_info(self):
        super().show_debug_info()
        c.bold_text(f'[{self.__class__.__name__}]')
        imgui.same_line()
        imgui.text(f'num_points: {self._debug_num_points}')
