import time
from typing import Optional

import imgui
import moderngl
import numpy as np

from gui import components as c
from gui import global_var as g
from gui.graphic import geometry
from gui.graphic import geometry_collection
from gui.modules.graphic_module import CameraFBT, GaussianBlenderFBT, FrameBufferTexture


class CubeSimple(CameraFBT):

    def __init__(self, name, width, height, channel=4, camera_type='orbit'):
        super().__init__(name, width, height, channel, camera_type)

        self.cube = geometry.SimpleCube('cube', size=(2, 2, 2))

    def render(self, **kwargs):
        self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST)
        self.fbo.use()
        self.fbo.clear(0, 0, 0, 0)

        self.cube.rotation = (g.mTime, g.mTime, g.mTime)
        self.cube.translation = (0.0, 0.0, -3.5)
        self.cube.render(self.camera)

    def show_debug_info(self):
        super().show_debug_info()


class CubeSimpleInstanced(CameraFBT):
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


def depth_texture_to_image_rgba(depth_texture):
    width = depth_texture.width
    height = depth_texture.height
    buffer = depth_texture.read()
    img_arr = np.frombuffer(buffer, dtype=np.float32).reshape((height, width))
    img_gray = (img_arr * 255).astype(np.uint8)
    img_rgba = np.stack([img_gray] * 4, axis=-1)
    return img_rgba


class SceneInfoRenderer(CameraFBT):

    def __init__(self, name, width, height, channel=4, camera_type='orbit'):
        super().__init__(name, width, height, channel, camera_type)
        self.geometry_collection = geometry_collection.PointCloudCollection('point_cloud_collection', self.camera)
        from gui.modules.graphic_module import SimpleTexture
        self.depth_simple_texture = SimpleTexture(width, height, channel)

    def set_points_arr(self, pos_arr, color_arr):
        self.geometry_collection.set_points_cloud(pos_arr, color_arr)

    def render(self, **kwargs):
        self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST | moderngl.PROGRAM_POINT_SIZE)
        self.ctx.point_size = 10
        self.fbo.use()
        self.fbo.clear()
        self.geometry_collection.render()
        self.depth_simple_texture.bilt_data(depth_texture_to_image_rgba(self.fbo.depth_attachment))
        g.mSharedTexture = self.depth_simple_texture

    def show_debug_info(self):
        super().show_debug_info()
        c.bold_text(f'[{self.__class__.__name__}]')
        self.geometry_collection.show_debug_info()


class GaussianRenderer(CameraFBT):
    """
        this renderer is used to render gaussian and normal geometries,

        it provides depth test for both gaussian and normal geometries,

        and combines them together using the depth information.

        the whole process is:
        1. render
        gaussian manger -> render -> gaussian color attachment(color)
        gaussian manager -> gaussian point cloud -> render to -> gaussian frame buffer texture(depth)
        geometry collection -> render to -> self (color and depth)
        2. blender using depth information
        gaussian color_attachment + gaussian frame buffer texture + self.fbo.color_attachment + self.fbo.depth_texture
        (color                         depth                           color                       depth)
        -> into -> blender frame buffer texture -> final image
        the depth info relies on GaussianPointCloud
        when the gaussian point cloud changed
        use GaussianPointCloud.update_gaussian_points() to update the point cloud
    """

    def __init__(self, name, width, height):

        super().__init__(name, width, height, 4, 'orbit_gaussian_camera')

        import torch
        self.torch = torch
        import numpy
        self.numpy = numpy

        self.gaussian_color_attachment = g.mWindowEvent.ctx.texture((width, height), 4)  # 3dgs image
        self.gaussianFBT = FrameBufferTexture('gaussian_FBT', width, height, 4)  # 绘制3dgs 点云的画布, 取深度信息
        self.gaussian_collection = geometry_collection.GaussianCollection('gaussian_collection', self.camera)  # 3dgs点云

        self.geometry_collection = geometry_collection.GeometryCollection('geometry_collection', self.camera)  # 常规物体的集合
        self.geometry_collection.add_geometry(geometry.SimpleCube('depth test cube', size=(0.5, 0.5, 10.0)))
        self.geometry_collection.add_geometry(geometry.Axis3D())

        self.blenderFBT = GaussianBlenderFBT('fs_FBT', width, height, 4)  # 混合渲染结果的画布

        # settings
        self.debug_render_gaussian = False
        self.debug_show_gaussian_pt_cloud = False  # 打开时预览Gaussian point cloud的color attachment
        self.debug_render_time_gap = 0.05  # default 20fps
        self._last_render_time = 0.0

    def set_gaussian_manager(self, gm):
        self.gaussian_collection.set_gaussian_manager(gm)

    def update_size(self, width, height):
        super().update_size(width, height)
        self.gaussian_color_attachment = g.mWindowEvent.ctx.texture((width, height), 4)
        self.blenderFBT.update_size(width, height)
        self.gaussianFBT.update_size(width, height)

    def render_gaussian(self):
        # render gaussian to self.gaussian_color_attachment
        curr_time = time.time()
        if time.time() - self._last_render_time < self.debug_render_time_gap:
            return
        # only render when time > time gap
        with self.torch.no_grad():
            image_rgb_arr: np.ndarray = self.gaussian_collection.render()
        self.gaussian_color_attachment.write(image_rgb_arr.tobytes())
        self._last_render_time = curr_time

    def render(self, **kwargs):
        self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST | moderngl.PROGRAM_POINT_SIZE)
        self.ctx.point_size = 10

        # render geometry to self.fbo.color_attachments[0]
        self.fbo.use()
        self.fbo.clear()
        self.geometry_collection.render()
        if not self.debug_show_gaussian_pt_cloud and not self.debug_render_gaussian:
            # 如果既不显示gaussian点云，也不显示高斯图像，到这里就可结束了
            return

        # 渲染3dgs点云数据
        self.gaussianFBT.fbo.use()
        self.gaussianFBT.fbo.clear()
        self.gaussian_collection.render()

        if not self.debug_render_gaussian:
            # 如果设置中不渲染gaussian image，则到这里结束
            return
        # 渲染gaussian
        self.render_gaussian()
        # blend textures
        self.blenderFBT.render(self.gaussian_color_attachment, self.gaussianFBT.fbo.depth_attachment,
                               self.fbo.color_attachments[0], self.fbo.depth_attachment)

    @property
    def texture(self):
        if self.debug_show_gaussian_pt_cloud:
            # 返回高斯点云
            return self.gaussianFBT.texture
        if self.debug_render_gaussian:
            # 返回混合图像
            return self.blenderFBT.texture
        # 返回几何体
        return self.fbo.color_attachments[0]

    @property
    def texture_id(self):
        return self.texture.glo

    def show_debug_info(self):
        super().show_debug_info()
        c.bold_text(f'[{self.__class__.__name__}]')
        _, self.debug_render_gaussian = imgui.checkbox('render gaussian', self.debug_render_gaussian)
        imgui.same_line()
        _, self.debug_show_gaussian_pt_cloud = imgui.checkbox('show gaussian pt cloud',
                                                              self.debug_show_gaussian_pt_cloud)
        imgui.same_line()
        imgui.set_next_item_width(g.GLOBAL_SCALE * 200)
        _, self.debug_render_time_gap = imgui.slider_float('render time gap', self.debug_render_time_gap, 0.0, 1.0)
        self.gaussian_collection.show_debug_info()

