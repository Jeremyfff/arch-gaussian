import math
import struct
import time

import imgui
import moderngl
import numpy as np
from pyrr import Matrix44

from gui import components as c
from gui import global_var as g
from gui.graphic import geometry
from gui.graphic import geometry_collection
from gui.modules import EventModule
from gui.modules.graphic_module import CameraFBT, GaussianBlenderFBT, FrameBufferTexture
from gui.utils import transform_utils


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

    def operation_panel(self):
        super().operation_panel()


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

    def operation_panel(self):
        super().operation_panel()


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

    def operation_panel(self):
        super().operation_panel()
        c.bold_text(f'[{self.__class__.__name__}]')

    def geometry_collection_operation_panel(self):
        self.geometry_collection.operation_panel()


class GaussianRenderer(CameraFBT):
    """
        this renderer is used to render gaussian and normal geometries,

        it provides depth test for both gaussian and normal geometries,

        and combines them together using the depth information.

        the whole process is:
        1. render
        gaussian manger -> render -> gaussian color attachment(color)
        gaussian manager -> gaussian point cloud -> render to -> gaussian frame buffer texture(depth)
        geometry collection and debug collection -> render to -> self (color and depth)
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

        # geometry collection, 常规物体的集合
        self.geometry_collection = geometry_collection.MyCustomGeometryCollection(
            name='geometry_collection', camera=self.camera
        )
        self.geometry_collection.add_geometry(geometry.Axis3D())

        # debug collection, debug物体的集合
        self.debug_collection = geometry_collection.DebugCollection(
            name='debug_collection', camera=self.camera
        )
        self.debug_collection.add_geometry(geometry.SimpleCube('depth test cube', size=(0.5, 0.5, 10.0)))

        # gaussian color attachment: texture for 3dgs
        self.gaussian_color_attachment = g.mWindowEvent.ctx.texture((width, height), 4)  # 3dgs image
        g.mWindowEvent.imgui.register_texture(self.gaussian_color_attachment)
        # gaussian frame buffer texture: fbo to draw 3dgs pt cloud (depth)
        self.gaussianFBT = FrameBufferTexture('gaussian_FBT', width, height, 4)
        # gaussian pt cloud collection
        self.gaussian_collection = geometry_collection.GaussianCollection(
            name='gaussian_collection', camera=self.camera, debug_collection=self.debug_collection
        )
        # blender frame buffer texture: 混合渲染结果的画布
        self.blenderFBT = GaussianBlenderFBT('fs_FBT', width, height, 4)

        # consts
        self.EMPTY_ARR = np.zeros((self.height, self.width, self.channel), dtype=np.uint8)

        # settings
        self.render_geometries = True
        self.render_gaussians = True
        self.render_debug_geometries = True

        self.debug_show_gaussian_pt_cloud = False  # 打开时预览Gaussian pt颜色信息
        self.debug_render_time_gap = 0.05  # default 20fps

        self.point_size = 10.0  # 渲染的点的大小
        # variables
        self._last_render_time = 0.0
        self._get_depth_in_frame = False  # 在这一帧获取深度
        self._get_depth_pos = [0, 0]  # 要获取深度的像素

        self.debug_last_click_pos = np.zeros(shape=(3), dtype=np.float32)

    def set_gaussian_manager(self, gm):
        self.gaussian_collection.set_gaussian_manager(gm)

    def update_size(self, width, height):
        super().update_size(width, height)
        g.mWindowEvent.imgui.remove_texture(self.gaussian_color_attachment)
        self.gaussian_color_attachment = g.mWindowEvent.ctx.texture((width, height), 4)
        g.mWindowEvent.imgui.register_texture(self.gaussian_color_attachment)
        self.blenderFBT.update_size(width, height)
        self.gaussianFBT.update_size(width, height)
        self.EMPTY_ARR = np.zeros((self.height, self.width, self.channel), dtype=np.uint8)

    def register_events(self, x, y, button):
        super().register_events(x, y, button)

    def unregister_events(self, x, y, button):
        super().unregister_events(x, y, button)

    def register_hovering_events(self):
        super().register_hovering_events()
        # 除了相机动作， 额外增加一些交互
        EventModule.register_mouse_release_callback(self._on_mouse_release_event)

    def unregister_hovering_events(self):
        super().unregister_hovering_events()
        EventModule.unregister_mouse_release_callback(self._on_mouse_release_event)

    def _on_mouse_release_event(self, x, y, button):
        """从父类触发, 仅在hover的时候起作用"""
        _ = self
        if button == 1:
            # 左键
            self._get_depth_in_frame = True  # 标记为true， 会在render时处理
            self._get_depth_pos = [int(x - g.mImagePos[0]), int(y - g.mImagePos[1])]

    def _mouse_release_callback(self):
        """传递给子对象"""

    def render_gaussian(self):
        # render gaussian to self.gaussian_color_attachment
        curr_time = time.time()
        if time.time() - self._last_render_time < self.debug_render_time_gap:
            return
        # only render when time > time gap
        with self.torch.no_grad():
            image_rgb_arr: np.ndarray = self.gaussian_collection.render_gaussian()
        if image_rgb_arr is None:
            image_rgb_arr = self.EMPTY_ARR
        self.gaussian_color_attachment.write(image_rgb_arr.tobytes())
        self._last_render_time = curr_time

    def render(self, **kwargs):
        self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST | moderngl.PROGRAM_POINT_SIZE)
        self.ctx.point_size = self.point_size
        # ============================================================================
        # region for debug purpose
        # cube_pos = self.camera.P + self.camera.f * 2
        # cube_pos = np.array([cube_pos[0], cube_pos[2], -cube_pos[1]])

        if self.debug_show_gaussian_pt_cloud:
            # 当需要预览gaussian pt cloud的颜色或深度信息时，只需要渲染以下内容
            self.gaussianFBT.fbo.use()
            self.gaussianFBT.fbo.clear()
            self.gaussian_collection.render()
            return
        # endregion
        # ============================================================================
        # region normal rendering
        """
        -render on self.fbo ->
        """
        self.fbo.use()
        self.fbo.clear()
        if self.render_geometries or self._get_depth_in_frame:
            self.geometry_collection.render()

        if self.render_debug_geometries or self._get_depth_in_frame:
            self.debug_collection.render()  # 正常渲染会执行清空操作
        else:
            self.debug_collection.geometries.clear()  # 即使没有render， 也要clear一下
        """
        -render on self.gaussian_color_attachment ->
        """
        if self.render_gaussians:
            # 渲染gaussian
            self.render_gaussian()
        """
        -render on self.gaussianFBT.fbo ->
        """
        if (self.render_geometries and self.render_gaussians) or self._get_depth_in_frame:
            # 渲染3dgs点云数据, 用于混合
            self.gaussianFBT.fbo.use()
            self.gaussianFBT.fbo.clear()
            self.gaussian_collection.render()
            # blend textures
            self.blenderFBT.render(self.gaussian_color_attachment, self.gaussianFBT.fbo.depth_attachment,
                                   self.fbo.color_attachments[0], self.fbo.depth_attachment)
        # endregion
        # ============================================================================
        # region 处理事件
        if self._get_depth_in_frame:
            print(f'calculating depth')
            self._get_depth_in_frame = False

            image_space_pos = self._get_depth_pos
            image_space_pos[0] = min(self.width - 1, image_space_pos[0])
            image_space_pos[0] = max(0, image_space_pos[0])
            image_space_pos[1] = min(self.height - 1, image_space_pos[1])
            image_space_pos[1] = max(0, image_space_pos[1])

            geo_depth_data = self.fbo.read(
                viewport=(image_space_pos[0], image_space_pos[1], 1, 1), components=1, attachment=-1, dtype='f4')
            geo_depth = struct.unpack('f', geo_depth_data)[0]
            gaussian_depth_data = self.gaussianFBT.fbo.read(
                viewport=(image_space_pos[0], image_space_pos[1], 1, 1), components=1, attachment=-1, dtype='f4')
            gaussian_depth = struct.unpack('f', gaussian_depth_data)[0]

            geo_linear_depth = transform_utils.depth_attachment_value_to_linear_depth(
                geo_depth, self.camera.projection.far, self.camera.projection.near
            )
            if geo_linear_depth is None:
                return
            gaussian_linear_depth = transform_utils.depth_attachment_value_to_linear_depth(
                gaussian_depth, self.camera.projection.far, self.camera.projection.near
            )

            m_model = np.array(Matrix44.from_eulers((-math.pi / 2, 0, 0), dtype='f4'))
            m_camera = np.array(self.camera.matrix).T
            m_proj = np.array(self.camera.projection.matrix)
            m_view = m_camera @ m_model

            gl_position = np.array([
                ((image_space_pos[0] / self.width) * 2 - 1) * geo_linear_depth,
                ((image_space_pos[1] / self.height) * 2 - 1) * geo_linear_depth,
                geo_linear_depth - 1,
                geo_linear_depth * 0.2

            ])
            print(gl_position)
            p = np.linalg.inv(m_proj) @ gl_position
            test_point = np.linalg.inv(m_view) @ p
            test_point[1] *= -1
            test_point[2] *= -1
            print(test_point)
            self.debug_last_click_pos = test_point[:3]

    @property
    def texture(self):

        if self.debug_show_gaussian_pt_cloud:
            # 返回高斯点云
            return self.gaussianFBT.texture
        if self.render_gaussians and self.render_geometries:
            # 返回混合图像
            return self.blenderFBT.texture
        if self.render_gaussians:
            # 返回高斯图像
            return self.gaussian_color_attachment
        return self.fbo.color_attachments[0]

    @property
    def texture_id(self):
        return self.texture.glo

    def operation_panel(self):
        # ====================super========================
        super().operation_panel()
        # ===============Gaussian Renderer=================
        c.bold_text('RENDERER SETTINGS')
        _, self.render_geometries = imgui.checkbox('render geometries', self.render_geometries)
        _, self.render_debug_geometries = imgui.checkbox('render debug geometries', self.render_debug_geometries)
        _, self.render_gaussians = imgui.checkbox('render gaussian', self.render_gaussians)
        _, self.debug_show_gaussian_pt_cloud = imgui.checkbox('show gaussian pt cloud',
                                                              self.debug_show_gaussian_pt_cloud)
        imgui.set_next_item_width(g.GLOBAL_SCALE * 200)
        _, self.debug_render_time_gap = imgui.slider_float('render time gap', self.debug_render_time_gap, 0.0, 1.0)
        imgui.set_next_item_width(g.GLOBAL_SCALE * 200)
        _, self.point_size = imgui.slider_float('point size', self.point_size, 1.0, 20.0)

    def geometry_collection_operation_panel(self):
        self.geometry_collection.operation_panel()

    def debug_collection_operation_panel(self):
        self.debug_collection.operation_panel()

    def gaussian_collection_operation_panel(self):
        self.gaussian_collection.operation_panel()

    def show_debug_info(self):
        # ====================super========================
        super().show_debug_info()
        # ===============Gaussian Renderer=================
        c.bold_text(f'[{self.__class__.__name__}]')
        # ===============collection=================
        self.geometry_collection.show_debug_info()
        self.gaussian_collection.show_debug_info()
