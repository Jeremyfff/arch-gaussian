import imgui
import moderngl

from gui import components as c
from gui import global_var as g
from gui.graphic import geometry
from gui.graphic import geometry_collection
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

        self.geometry_collection = geometry_collection.PointCloudCollection(self.camera)

    def set_points_arr(self, pos_arr, color_arr):
        self.geometry_collection.set_points_cloud(pos_arr, color_arr)

    def render(self, **kwargs):
        self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST | moderngl.PROGRAM_POINT_SIZE)
        self.ctx.point_size = 10
        self.fbo.use()
        self.fbo.clear()
        self.geometry_collection.render()

    def show_debug_info(self):
        super().show_debug_info()
        c.bold_text(f'[{self.__class__.__name__}]')
        self.geometry_collection.show_debug_info()
