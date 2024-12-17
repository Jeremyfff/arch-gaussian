import logging
import os
import struct
import time

import imgui
import moderngl
import numpy as np

from gui.components import c
from gui.global_app_state import g
from gui.global_info import *
from gui.global_info import RESOURCES_DIR
from gui.graphic import geometry
from gui.graphic import geometry_collection
from gui.graphic.material_lib import MaterialLib
from gui.modules import EventModule
from gui.modules.graphic_module import CameraFBT, GaussianBlenderFBT, GaussianColorFBT, FrameBufferTexture
from gui.user_data import user_data
from gui.utils import transform_utils


def record_last_render_time(func):
    def wrapper(self: "FrameBufferTexture", *args, **kwargs):
        self.last_render_time = time.time()
        return func(self, *args, **kwargs)

    return wrapper


def depth_texture_to_image_rgba(depth_texture):
    width = depth_texture.width
    height = depth_texture.height
    buffer = depth_texture.read()
    img_arr = np.frombuffer(buffer, dtype=np.float32).reshape((height, width))
    img_gray = (img_arr * 255).astype(np.uint8)
    img_rgba = np.stack([img_gray] * 4, axis=-1)
    return img_rgba


class IRenderer(CameraFBT):
    _InstanceCount = 0

    def __init__(self, name, width, height):
        super().__init__(f"{name}({IRenderer._InstanceCount})", width, height)
        IRenderer._InstanceCount += 1
        # ==========================================================================================
        # ||                                 Import Modules                                       ||
        # ==========================================================================================
        import torch
        self.torch = torch

        # ==========================================================================================
        # ||                              Geometry Collections                                    ||
        # ==========================================================================================
        # renderer可以拥有下面四种不同的物体集合，根据需要在子类中进行设置, 其中必须包含scene_basic_geometry_collection
        self._scene_basic_geometry_collection: geometry_collection.SceneBasicCollection = geometry_collection.SceneBasicCollection(f'scene_basic_{name}', self)
        self._geometry_collection: geometry_collection.EditableGeometryCollection = geometry_collection.EditableGeometryCollection(f"geometry_collection_{name}", self)
        self._gaussian_collection: geometry_collection.GaussianCollection = geometry_collection.GaussianCollection(f"gaussian_collection_{name}", self)
        self._debug_collection: geometry_collection.DebugCollection = geometry_collection.DebugCollection(f"debug_collection_{name}", self)

        # geometries in collections
        self._dlight = self.scene_basic_geometry_collection.directional_light
        # 添加基础物体
        num = 1
        pos_arr = np.random.rand(num, 3).astype(np.float32)
        color_arr = np.random.rand(num, 4).astype(np.float32)
        self.point_cloud = geometry.PointCloud("_SceneInfoRenderer_PointCloud", pos_arr, color_arr)
        self.geometry_collection.add_geometry(self.point_cloud)

        self._mesh_geo = self.geometry_collection.add_geometry(geometry.Mesh3D(
            "_AutoAdded_Mesh",
            os.path.join(RESOURCES_DIR, "models/unit_sphere.obj"),
            MaterialLib.GetDefaultMat_Lit().copy("_Mat_MyMesh")
        ))
        self._ground_geo: geometry.BaseGeometry3D = self.geometry_collection.add_geometry(
            geometry.SimpleCube("_Ground")
        )
        self._ground_geo.transform.scale = (100.0, 100.0, 0.1)
        self._ground_geo.transform.translation = (0, 0, -1.1)

        # ==========================================================================================
        # ||                              Frame Buffer Textures                                   ||
        # ==========================================================================================
        self._shadowmap_fbt = FrameBufferTexture(f"~{self.name}_shadowmap_fbt", 1000, 1000, with_depth=True)
        self._shadowmap_sampler = self.ctx.sampler(border_color=(1, 1, 1, 1), texture=self._shadowmap_fbt.fbo.depth_attachment)
        self.gaussianColorFBT: GaussianColorFBT = GaussianColorFBT(f"~{self.name}_Gaussian_color_fbt", width, height)
        self.blenderFBT: GaussianBlenderFBT = GaussianBlenderFBT(f"~{self.name}_gaussian_blender_fbt", width, height, 4)

        # ==========================================================================================
        # ||                             Uniform Buffer Objects                                   ||
        # ==========================================================================================
        self._common_data_ubo = self.ctx.buffer(reserve=self.common_data_ubo_size)
        self._camera_data_ubo = self.ctx.buffer(reserve=self.camera_data_ubo_size)
        self._light_data_ubo = self.ctx.buffer(reserve=self.light_data_ubo_size)
        self.update_common_data_ubo()
        self.update_camera_data_ubo()
        self.update_light_data_ubo()
        self._common_data_ubo.bind_to_uniform_block(1)
        self._camera_data_ubo.bind_to_uniform_block(2)
        self._light_data_ubo.bind_to_uniform_block(3)

        # ==========================================================================================
        # ||                              Settings and Variables                                  ||
        # ==========================================================================================
        self._last_render_time = 0.0
        self._get_depth_in_frame = False  # 在这一帧获取深度
        self._get_depth_pos = [0, 0]  # 要获取深度的像素

        self.debug_last_click_pos = np.zeros(shape=(3,), dtype=np.float32)

        # Settings Validation
        if not isinstance(user_data.renderer_downsample, int):
            user_data.renderer_downsample = int(user_data.renderer_downsample)

        self._downsample_options = [1, 2, 4, 8]
        self._downsample_options_str = ["1 (Best Quality)", "2 (Balanced)", "4 (Better Performance)", "8 (Best Performance)"]
        try:
            self._curr_downsample_option_idx = self._downsample_options.index(user_data.renderer_downsample)
        except ValueError:
            logging.error(f"cannot find {user_data.renderer_downsample} in self._gaussian_renderer_downsample_options ({self._downsample_options})")
            self._curr_downsample_option_idx = -1

    def update(self):
        self.scene_basic_geometry_collection.update()
        self.geometry_collection.update()
        self.gaussian_collection.update()
        self.debug_collection.update()

    @record_last_render_time
    def render(self, **kwargs):
        # ============================================================================
        if user_data.renderer_max_frame_rate < 1:
            return

        curr_time = g.mTime
        if (curr_time - self._last_render_time) < 1.0 / user_data.renderer_max_frame_rate:
            return
        self._last_render_time = curr_time
        # ============================================================================
        self.ctx.enable(moderngl.CULL_FACE | moderngl.DEPTH_TEST | moderngl.PROGRAM_POINT_SIZE)
        self.ctx.point_size = user_data.renderer_point_size

        # Update UBO
        self.update_common_data_ubo()
        self.update_light_data_ubo()

        # region  ================== PASS 1 : Shadow Map ====================
        self._shadowmap_fbt.last_render_time = time.time()
        self._shadowmap_fbt.fbo.use()
        self._shadowmap_fbt.fbo.clear()

        if self.dlight.active:
            self.update_camera_data_ubo_for_shadowmap()
            self.geometry_collection.render_shadowmap(self.dlight)
        # endregion

        # region  ================== PASS 2 : Main ====================
        self.fbo.use()
        self.fbo.clear(alpha=1.0)
        self.update_camera_data_ubo()

        self._shadowmap_sampler.use(PRESERVED_TEXTURE_LOCATIONS["_ShadowMap"])

        self.scene_basic_geometry_collection.render()
        if user_data.can_render_geometry:
            self.geometry_collection.render()
        if user_data.can_render_debug_geometry:
            self.debug_collection.render()
        if user_data.can_render_gaussian:
            self.gaussianColorFBT.render(self.gaussian_collection, self.fbo.depth_attachment)
            self.blenderFBT.render(self.fbo.color_attachments[0], self.gaussianColorFBT.fbo.color_attachments[0])

        # endregion

        # region Clean up
        self.ctx.clear_samplers()
        # endregion

    @property
    def texture(self):
        if user_data.can_render_gaussian:
            return self.blenderFBT.texture
        return self.fbo.color_attachments[0]

    @property
    def texture_id(self):
        return self.texture.glo

    @property
    def scene_basic_geometry_collection(self):
        return self._scene_basic_geometry_collection

    @property
    def geometry_collection(self):
        return self._geometry_collection

    @property
    def gaussian_collection(self):
        return self._gaussian_collection

    @property
    def debug_collection(self):
        return self._debug_collection

    @property
    def dlight(self):
        return self._dlight

    def update_size(self, width, height):
        width = int(width)
        height = int(height)

        super().update_size(width, height)
        self.gaussianColorFBT.update_size(width, height)
        self.blenderFBT.update_size(width, height)

    def set_points_arr(self, pos_arr, color_arr):
        self.geometry_collection.remove_geometry(self.point_cloud)
        pos_arr = pos_arr.astype(np.float32)
        color_arr = color_arr.astype(np.float32)
        self.point_cloud = geometry.PointCloud("_SceneInfoRenderer_PointCloud", pos_arr, color_arr)

    def set_gaussian_manager(self, gm):
        self.gaussian_collection.set_gaussian_manager(gm)

    def is_gaussian_renderer(self):
        return self.gaussian_collection is not None  # 当存在Gaussian Collection时，为高斯渲染器

    def show_geometry_collection_panel(self):
        if self.geometry_collection is None:
            return
        self.geometry_collection.operation_panel()

    def show_scene_basic_geometry_collection_panel(self):
        if self.scene_basic_geometry_collection is None:
            return
        self.scene_basic_geometry_collection.operation_panel()

    def show_gaussian_collection_panel(self):
        if self.gaussian_collection is None:
            return
        self.gaussian_collection.operation_panel()

    def show_debug_collection_panel(self):
        if self.debug_collection is None:
            return
        self.debug_collection.operation_panel()

    def operation_panel(self):
        super().operation_panel()
        c.bold_text(f'[{self.__class__.__name__}] Settings')
        imgui.set_next_item_width(g.global_scale * 200)
        _, user_data.renderer_max_frame_rate = imgui.slider_int('max frame rate', user_data.renderer_max_frame_rate, 0, 60)
        imgui.set_next_item_width(g.global_scale * 200)
        _, user_data.renderer_point_size = imgui.slider_float('point size', user_data.renderer_point_size, 1.0, 20.0)
        imgui.set_next_item_width(g.global_scale * 200)
        changed, self._curr_downsample_option_idx = imgui.combo("gaussian downsample", self._curr_downsample_option_idx, self._downsample_options_str)
        if changed:
            last_value = user_data.renderer_downsample
            new_value = self._downsample_options[self._curr_downsample_option_idx]
            if last_value != new_value:
                user_data.renderer_downsample = new_value
                EventModule.resize(*g.mWindowSize)

    def show_debug_info(self):
        super().show_debug_info()
        c.bold_text(f'[{self.__class__.__name__}]')
        self.scene_basic_geometry_collection.show_debug_info()
        self.geometry_collection.show_debug_info()
        self.debug_collection.show_debug_info()
        self.gaussian_collection.show_debug_info()

    # region common_data_ubo
    @property
    def common_data_ubo_size(self):
        return 16 + 64 + 16  # mat4 + vec3 (std140, align to 16 bytes)

    def update_common_data_ubo(self):
        _ = self.camera.matrix  # calculate matrix to update camera position, see OrbitCamera
        time_data: bytes = struct.pack('f', g.mTime)
        m_world_data: bytes = transform_utils.world_matrix.astype("f4").tobytes()
        cam_pos_data: bytes = transform_utils.from_gl_space(self.camera.position).astype("f4").tobytes()
        self._common_data_ubo.write(time_data, 0)
        self._common_data_ubo.write(m_world_data, 16)
        self._common_data_ubo.write(cam_pos_data, 80)

    # endregion

    # region camera_data_ubo
    @property
    def camera_data_ubo_size(self):
        return 64 + 64 + 16

    def update_camera_data_ubo(self):
        m_camera_data: bytes = self.camera.matrix.astype("f4").tobytes()
        m_proj_data: bytes = self.camera.projection.matrix.astype("f4").tobytes()
        cam_pos_data: bytes = transform_utils.from_gl_space(self.camera.position).astype("f4").tobytes()
        self._camera_data_ubo.write(m_camera_data, 0)
        self._camera_data_ubo.write(m_proj_data, 64)
        self._camera_data_ubo.write(cam_pos_data, 128)

    def update_camera_data_ubo_for_shadowmap(self):
        m_camera_data: bytes = self.dlight.m_camera.astype("f4").tobytes()
        m_proj_data: bytes = self.dlight.m_projection.astype("f4").tobytes()
        cam_pos_data: bytes = self.dlight.transform.translation.astype("f4").tobytes()
        self._camera_data_ubo.write(m_camera_data, 0)
        self._camera_data_ubo.write(m_proj_data, 64)
        self._camera_data_ubo.write(cam_pos_data, 128)

    # endregion

    # region light_data_ubo
    @property
    def light_data_ubo_size(self):
        return 64 + 16 + 16

    def update_light_data_ubo(self):
        m_depth_data = self.dlight.m_depth.astype("f4").tobytes()  # Matrix44
        dir_data = self.dlight.direction.astype("f4").tobytes()  # Vector3
        color_data = self.dlight.color.astype("f4").tobytes()  # Vector3

        self._light_data_ubo.write(m_depth_data, 0)
        self._light_data_ubo.write(dir_data, 64)
        self._light_data_ubo.write(color_data, 80)

    # endregion
