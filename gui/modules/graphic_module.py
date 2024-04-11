import logging
from abc import abstractmethod
from typing import Literal, Union

import imgui
import moderngl
import numpy as np
from moderngl_window.scene.camera import KeyboardCamera, OrbitCamera

from gui import components as c
from gui import global_var as g
from gui.graphic import geometry
from gui.graphic.camera_behaviour import OrbitCameraBehaviour, OrbitGaussianCameraBehaviour, FreeCameraBehaviour
from gui.graphic.cameras import OrbitGaussianCamera

np.set_printoptions(precision=2, suppress=True)


class SimpleTexture:
    def __init__(self, width, height, channel):
        self.ctx: moderngl.Context = g.mWindowEvent.ctx

        self.texture: moderngl.Texture = self.ctx.texture((width, height), channel)
        g.mWindowEvent.imgui.register_texture(self.texture)

    def bilt_data(self, arr_in_uint8: np.ndarray):
        height, width, channel = arr_in_uint8.shape
        if height != self.texture.height or width != self.texture.width or channel != self.texture.components:
            g.mWindowEvent.imgui.remove_texture(self.texture)
            self.texture = self.ctx.texture((width, height), channel)
            g.mWindowEvent.imgui.register_texture(self.texture)
        self.texture.write(arr_in_uint8.tobytes())


class FrameBufferTexture:
    """
    使用modernGL 的 FrameBuffer作为渲染画布的高级Texture对象
    此类为基类， 实现了基础属性的获取与修改，支持改变texture的尺寸并自动注册和销毁
    要对该Texture进行修改，需要继承该类并对render方法进行修改
    """

    def __init__(self, name, width, height, channel=4):
        self.name = name
        self.width, self.height, self.channel = width, height, channel

        self.ctx: moderngl.Context = g.mWindowEvent.ctx
        self.wnd = g.mWindowEvent.wnd
        # 新建一个frame buffer object， 在上面进行渲染绘图
        self.fbo = self.ctx.framebuffer(color_attachments=self.ctx.texture((width, height), 4),
                                        depth_attachment=self.ctx.depth_texture((width, height)))  # frame buffer object
        g.mWindowEvent.imgui.register_texture(self.fbo.color_attachments[0])
        g.mWindowEvent.imgui.register_texture(self.fbo.depth_attachment)

    @property
    def texture(self):
        return self.fbo.color_attachments[0]

    @property
    def texture_id(self):
        return self.texture.glo

    @staticmethod
    def load_program(path):
        return g.mWindowEvent.load_program(path)

    def update_size(self, width, height):
        g.mWindowEvent.imgui.remove_texture(self.fbo.color_attachments[0])
        g.mWindowEvent.imgui.remove_texture(self.fbo.depth_attachment)
        self.width, self.height = width, height

        self.fbo = self.ctx.framebuffer(color_attachments=self.ctx.texture((width, height), 4),
                                        depth_attachment=self.ctx.depth_texture((width, height)))
        g.mWindowEvent.imgui.register_texture(self.fbo.color_attachments[0])
        g.mWindowEvent.imgui.register_texture(self.fbo.depth_attachment)
        logging.debug(f'texture size updated to {self.width, self.height}, '
                      f'color attachment id = {self.fbo.color_attachments[0].glo}, '
                      f'depth_texture id = {self.fbo.depth_attachment.glo}')

    @abstractmethod
    def render(self, **kwargs):
        pass

    @abstractmethod
    def show_debug_info(self):
        c.bold_text('[FrameBufferTexture]')
        imgui.same_line()
        imgui.text(f'width: {self.width} height: {self.height} channel: {self.channel}')

    @abstractmethod
    def operation_panel(self):
        pass

    def frame_to_arr(self):
        buffer = self.texture.read()
        img_arr = np.frombuffer(buffer, dtype=np.uint8).reshape(
            (self.height, self.width, self.channel))
        return img_arr

    def frame_to_file(self, path):
        from PIL import Image
        img_arr = self.frame_to_arr()
        image = Image.fromarray(img_arr)
        image.save(path)


class CameraFBT(FrameBufferTexture):
    """自由摄像机 模板"""

    def __init__(self, name, width, height, channel=4,
                 camera_type: Literal['free', 'orbit', 'orbit_gaussian_camera'] = 'orbit'):
        super().__init__(name, width, height, channel)
        self.camera_type = camera_type
        if camera_type == 'free':
            self.camera_behaviour = FreeCameraBehaviour()
        elif camera_type == 'orbit':
            self.camera_behaviour = OrbitCameraBehaviour()
        elif camera_type == 'orbit_gaussian_camera':
            self.camera_behaviour = OrbitGaussianCameraBehaviour(width, height)
        self.camera: Union[OrbitCamera, KeyboardCamera, OrbitGaussianCamera] = self.camera_behaviour.camera

    def update_size(self, width, height):
        super().update_size(width, height)
        self.camera_behaviour.update_size(width, height)

    def register_events(self, x, y, button):
        self.camera_behaviour.register_events(x, y, button)

    def unregister_events(self, x, y, button):
        self.camera_behaviour.unregister_events(x, y, button)

    def register_hovering_events(self):
        self.camera_behaviour.register_hovering_events()

    def unregister_hovering_events(self):
        self.camera_behaviour.unregister_hovering_events()

    @abstractmethod
    def render(self, **kwargs):
        pass

    @abstractmethod
    def show_debug_info(self):
        super().show_debug_info()
        c.bold_text('[CameraFrameBuffer]')
        self.camera_behaviour.show_debug_info()

    @abstractmethod
    def operation_panel(self):
        super().operation_panel()


class GaussianBlenderFBT(FrameBufferTexture):
    def __init__(self, name, width, height, channel=4):
        super().__init__(name, width, height, channel)
        self.quad_fs = geometry.QuadFullScreen('full_screen_quad', 'programs/gaussian_blender.glsl')
        self.quad_fs.prog['gaussian_color_texture'].value = 0
        self.quad_fs.prog['gaussian_depth_texture'].value = 1
        self.quad_fs.prog['geometry_color_texture'].value = 2
        self.quad_fs.prog['geometry_depth_texture'].value = 3

    def update_prog(self, key, value):
        self.quad_fs.prog[key].value = value

    def render(self, gaussian_color_attachment, gaussian_depth_texture,
               geometry_color_attachment, geometry_depth_texture):
        self.fbo.use()
        self.fbo.clear()
        gaussian_color_attachment.use(location=0)
        gaussian_depth_texture.use(location=1)
        geometry_color_attachment.use(location=2)
        geometry_depth_texture.use(location=3)
        self.quad_fs.render(None)

    def show_debug_info(self):
        super().show_debug_info()

    def operation_panel(self):
        super().operation_panel()
