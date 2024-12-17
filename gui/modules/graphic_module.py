import logging
import time
import uuid
from abc import abstractmethod
from typing import Literal, Union, Optional

import imgui
import moderngl
import moderngl_window.scene.camera
import numpy as np
from OpenGL import GL
from cuda import cudart as cu
from moderngl_window.scene.camera import KeyboardCamera, OrbitCamera

from gui.components import c
from gui.global_app_state import g
from gui.graphic import geometry
from gui.graphic.camera_behaviour import OrbitCameraBehaviour
from gui.graphic.cameras import GL_3DGS_Camera
from gui.graphic.material import IMaterial
from gui.graphic.material_lib import MaterialLib
from gui.modules import BaseModule

np.set_printoptions(precision=2, suppress=True)

__runtime__ = True
if not __runtime__:
    from gui.graphic.geometry_collection import GaussianCollection


def record_last_render_time(func):
    def wrapper(self: "FrameBufferTexture", *args, **kwargs):
        self.last_render_time = time.time()
        return func(self, *args, **kwargs)
    return wrapper


class GraphicModule(BaseModule):
    registered_simple_textures: list["SimpleTexture"] = []
    registered_frame_buffer_textures: list["FrameBufferTexture"] = []

    @classmethod
    def m_init(cls):
        pass

    @classmethod
    def register_simple_texture(cls, texture: "SimpleTexture"):
        cls.registered_simple_textures.append(texture)

    @classmethod
    def unregister_simple_texture(cls, texture: "SimpleTexture"):
        cls.registered_simple_textures.remove(texture)

    @classmethod
    def register_fbt(cls, fbt: "FrameBufferTexture"):
        cls.registered_frame_buffer_textures.append(fbt)

    @classmethod
    def unregister_fbt(cls, fbt: "FrameBufferTexture"):
        cls.registered_frame_buffer_textures.remove(fbt)


class SimpleTexture:
    def __init__(self, name, width, height, channel, dtype="f1"):
        self.name = name
        self.ctx: moderngl.Context = g.mWindowEvent.ctx

        self.texture: moderngl.Texture = self.ctx.texture((width, height), channel, dtype=dtype)
        g.mWindowEvent.imgui.register_texture(self.texture)
        GraphicModule.register_simple_texture(self)

    @property
    def glo(self):
        return self.texture.glo

    def use(self, location=0):
        self.texture.use(location)

    @property
    def width(self):
        return self.texture.width

    @property
    def height(self):
        return self.texture.height

    def __del__(self):
        self.texture.release()
        g.mWindowEvent.imgui.remove_texture(self.texture)
        GraphicModule.unregister_simple_texture(self)
        del self.texture


class FrameBufferTexture:
    """
    使用modernGL 的 FrameBuffer作为渲染画布的高级Texture对象
    此类为基类， 实现了基础属性的获取与修改，支持改变texture的尺寸并自动注册和销毁
    要对该Texture进行修改，需要继承该类并对render方法进行修改
    """

    def __init__(self, name, width, height, channel=4, with_depth=True):
        self.name = name
        self.width, self.height, self.channel = width, height, channel
        self.with_depth = with_depth

        self.ctx: moderngl.Context = g.mWindowEvent.ctx
        self.wnd = g.mWindowEvent.wnd

        self.last_render_time = -1

        # 新建一个frame buffer object， 在上面进行渲染绘图

        self._fbo = self.ctx.framebuffer(color_attachments=self.ctx.texture((width, height), channel),
                                         depth_attachment=self.ctx.depth_texture((width, height)) if with_depth else None)  # frame buffer object
        g.mWindowEvent.imgui.register_texture(self.fbo.color_attachments[0])
        if with_depth:
            g.mWindowEvent.imgui.register_texture(self.fbo.depth_attachment)
        GraphicModule.register_fbt(self)

    @property
    def texture(self):
        return self.fbo.color_attachments[0]

    @property
    def texture_id(self):
        return self.texture.glo

    @property
    def fbo(self):
        # self.last_render_time = time.time()
        return self._fbo

    @fbo.setter
    def fbo(self, value):
        self._fbo = value

    def update_size(self, width, height):
        if width == self.width and height == self.height:
            return

        g.mWindowEvent.imgui.remove_texture(self.fbo.color_attachments[0])
        self.fbo.color_attachments[0].release()  # manually release

        if self.with_depth:
            g.mWindowEvent.imgui.remove_texture(self.fbo.depth_attachment)
            self.fbo.depth_attachment.release()

        self.width, self.height = width, height

        self.fbo = self.ctx.framebuffer(color_attachments=self.ctx.texture((width, height), self.channel),
                                        depth_attachment=self.ctx.depth_texture((width, height)) if self.with_depth else None)
        g.mWindowEvent.imgui.register_texture(self.fbo.color_attachments[0])
        if self.with_depth:
            g.mWindowEvent.imgui.register_texture(self.fbo.depth_attachment)

    @abstractmethod
    def render(self, **kwargs):
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

    def __del__(self):
        g.mWindowEvent.imgui.remove_texture(self.fbo.color_attachments[0])
        self.fbo.color_attachments[0].release()  # manually release

        if self.with_depth:
            g.mWindowEvent.imgui.remove_texture(self.fbo.depth_attachment)
            self.fbo.depth_attachment.release()
        GraphicModule.unregister_fbt(self)


class CameraFBT(FrameBufferTexture):
    """自由摄像机 模板"""

    def __init__(self, name, width, height):
        super().__init__(name, width, height, 4, True)
        self.camera_behaviour = OrbitCameraBehaviour(width, height)
        self.camera: Union[moderngl_window.scene.camera.Camera, OrbitCamera, KeyboardCamera, GL_3DGS_Camera] = self.camera_behaviour.camera

    def update_size(self, width, height):
        if not isinstance(width, int):
            width = int(width)
        if not isinstance(height, int):
            height = int(height)
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
        c.bold_text('[CameraFrameBuffer]')
        self.camera_behaviour.show_debug_info()

    @abstractmethod
    def operation_panel(self):
        pass


class GaussianColorFBT(FrameBufferTexture):
    def __init__(self, name, width, height):
        super().__init__(name, width, height, 4, with_depth=False)

        import torch
        self.torch = torch

        _mat = MaterialLib.GetDefaultMat_GaussianColor()
        self.quad_fs = geometry.QuadFullScreen(name=f"{name}_full_screen_quad", material=_mat)

        # register color channels
        self.gaussian_color_channels = []
        self.gaussian_color_channels_cuda = []
        for i in range(self.channel):
            tex = g.mWindowEvent.ctx.texture((width, height), 1, dtype='f4')
            self.gaussian_color_channels.append(tex)
            # g.mWindowEvent.imgui.register_texture(tex)
            _, cuda_image = cu.cudaGraphicsGLRegisterImage(
                tex.glo,
                GL.GL_TEXTURE_2D,
                cu.cudaGraphicsRegisterFlags.cudaGraphicsRegisterFlagsWriteDiscard,
            )
            self.gaussian_color_channels_cuda.append(cuda_image)

        # create depth tensor for opaque depth data
        self.opaque_depth_buffer = g.mWindowEvent.ctx.buffer(None, (width * height * 4), False)
        _, self.opaque_depth_cuda = cu.cudaGraphicsGLRegisterBuffer(
            self.opaque_depth_buffer.glo,
            cu.cudaGraphicsRegisterFlags.cudaGraphicsRegisterFlagsNone
        )
        self.opaque_depth_tensor: torch.Tensor = torch.ones(size=(1, height, width), dtype=torch.float32, requires_grad=False, device='cuda')

    def update_size(self, width, height):
        if width == self.width and height == self.height:
            return
        super().update_size(width, height)
        # update colors size
        for i in range(self.channel):
            self.gaussian_color_channels[i].release()
            self.gaussian_color_channels[i] = g.mWindowEvent.ctx.texture((width, height), 1, dtype='f4')
            _, self.gaussian_color_channels_cuda[i] = cu.cudaGraphicsGLRegisterImage(
                self.gaussian_color_channels[i].glo,
                GL.GL_TEXTURE_2D,
                cu.cudaGraphicsRegisterFlags.cudaGraphicsRegisterFlagsWriteDiscard,
            )
        # update depth
        self.opaque_depth_buffer.release()
        self.opaque_depth_buffer = g.mWindowEvent.ctx.buffer(None, (width * height * 4), False)
        err, self.opaque_depth_cuda = cu.cudaGraphicsGLRegisterBuffer(
            self.opaque_depth_buffer.glo,
            cu.cudaGraphicsRegisterFlags.cudaGraphicsRegisterFlagsNone
        )
        if err != cu.cudaError_t.cudaSuccess:
            raise Exception(str(err))

        self.opaque_depth_tensor = self.torch.ones(size=(1, height, width), dtype=self.torch.float32, requires_grad=False, device='cuda')

    @record_last_render_time
    def render(self, gaussian_collection: "GaussianCollection", opaque_depth: moderngl.Texture):
        """
        opaque_depth.dtype == 'f4', components == 1
        :param gaussian_collection:
        :param opaque_depth:
        :return:
        """

        # copy depth buffer to self.opaque_depth_tex
        opaque_depth.read_into(self.opaque_depth_buffer)

        # Mem Cpy : opaque depth buffer -> opaque depth tensor
        # tensorChannel, tensorHeight, tensorWidth = self.opaque_depth_tensor.shape
        # elementSize = self.opaque_depth_tensor.element_size()
        _ = cu.cudaGraphicsMapResources(1, self.opaque_depth_cuda, cu.cudaStreamLegacy)
        # _, array = cu.cudaGraphicsSubResourceGetMappedArray(self.opaque_depth_cuda, 0, 0)
        err, pointer, size = cu.cudaGraphicsResourceGetMappedPointer(self.opaque_depth_cuda)

        err = cu.cudaMemcpy(
            self.opaque_depth_tensor.data_ptr(),
            pointer,
            size,
            cu.cudaMemcpyKind.cudaMemcpyDeviceToDevice,
        )
        if not isinstance(err, tuple) and err != cu.cudaError_t.cudaSuccess:
            raise Exception(str(err))
        _ = cu.cudaGraphicsUnmapResources(1, self.opaque_depth_cuda, cu.cudaStreamLegacy)

        # Invoke CUDA/C++ to Render Gaussian
        image_tensor = gaussian_collection.render_gaussian(opaque_depth=self.opaque_depth_tensor)
        if image_tensor is None:
            return

        # Copy color from cuda to opengl texture
        tensorChannel, tensorHeight, tensorWidth = image_tensor.shape
        elementSize = image_tensor.element_size()
        for i in range(self.channel):
            _ = cu.cudaGraphicsMapResources(1, self.gaussian_color_channels_cuda[i], cu.cudaStreamLegacy)
            _, array = cu.cudaGraphicsSubResourceGetMappedArray(self.gaussian_color_channels_cuda[i], 0, 0)
            _ = cu.cudaMemcpy2DToArrayAsync(
                array,
                0,
                0,
                image_tensor.data_ptr() + tensorWidth * tensorHeight * elementSize * i,
                tensorWidth * elementSize,
                tensorWidth * elementSize,
                tensorHeight,
                cu.cudaMemcpyKind.cudaMemcpyDeviceToDevice,
                cu.cudaStreamLegacy,
            )
            _ = cu.cudaGraphicsUnmapResources(1, self.gaussian_color_channels_cuda[i], cu.cudaStreamLegacy)

        # render to comp color channels
        self.fbo.use()
        self.fbo.clear()
        for i in range(self.channel):
            self.gaussian_color_channels[i].use(location=i)
        self.quad_fs.render()


class GaussianBlenderFBT(FrameBufferTexture):
    def __init__(self, name, width, height, channel=4):
        super().__init__(name, width, height, channel, with_depth=True)

        _mat = MaterialLib.GetDefaultMat_GaussianBlender()
        self.quad_fs = geometry.QuadFullScreen(f'{name}_full_screen_quad', _mat)

    @record_last_render_time
    def render(self, geometry_color_attachment, gaussian_color_attachment):
        self.fbo.use()
        self.fbo.clear()
        geometry_color_attachment.use(location=0)
        gaussian_color_attachment.use(location=1)

        self.quad_fs.render()


class BlurFBT(FrameBufferTexture):
    """ blur"""

    def __init__(self, name, width, height, channel=4, has_prev=True):
        super().__init__(name, width, height, channel, False)

        _mat = MaterialLib.GetDefaultMat_FSBlur()
        self.quad_fs = geometry.QuadFullScreen(f'{name}_full_screen_quad', _mat)
        if has_prev:
            self.prev_step = BlurFBT(f"{name}(auto generated h)", width, height, channel, False)  # has prev must be False here to avoid recursive
        else:
            self.prev_step = None

    def update_size(self, width, height):
        if self.prev_step:
            self.prev_step.update_size(width, height)

        super().update_size(width, height)

    @record_last_render_time
    def one_step_render(self, texture: moderngl.Texture, radius: float, direction: tuple[float, float], ky=0.0, by=1.0, kx=0.0, bx=1.0, tint0=(1, 1, 1, 1), tint1=(1, 1, 1, 1)):
        self.fbo.use()
        self.fbo.clear()
        self.quad_fs.material['_Texture'] = 0
        self.quad_fs.material['_Dir'] = (float(direction[0]) / self.width, float(direction[1]) / self.height)
        self.quad_fs.material['_Radius'] = radius

        self.quad_fs.material['_K_Y'] = ky
        self.quad_fs.material['_B_Y'] = by
        self.quad_fs.material['_K_X'] = kx
        self.quad_fs.material['_B_X'] = bx
        self.quad_fs.material['_Tint0'] = tint0
        self.quad_fs.material['_Tint1'] = tint1

        texture.use(location=0)
        self.quad_fs.render()

    @record_last_render_time
    def render(self, texture: moderngl.Texture, radius: float, ky=0.0, by=1.0, kx=0.0, bx=1.0, tint0=(1, 1, 1, 0), tint1=(1, 1, 1, 0)):
        if self.prev_step:
            self.prev_step.one_step_render(texture, radius, (1, 0), ky, by, kx, bx, tint0, tint1)
            texture = self.prev_step.texture

        self.one_step_render(texture, radius, (0, 1), ky, by, kx, bx, tint0, tint1)


class RoundedButtonFBT(FrameBufferTexture):
    def __init__(self, width, height):
        super().__init__(f"rounded_button_{uuid.uuid4()}", width, height, 4, False)
        _mat = MaterialLib.GetDefaultMat_RoundedButton()
        self.quad_fs = geometry.QuadFullScreen(f"{self.name}_full_screen_quad", _mat)

    @record_last_render_time
    def render(self, t: float, rounding: float = 4):
        """

        :param t: range(0, 1)
        :param rounding: in pixel
        :return:
        """
        self.fbo.use()
        self.fbo.clear(1, 1, 1, 0)
        self.quad_fs.material['_T'] = t
        self.quad_fs.material['_Resolution'] = (self.width, self.height)
        self.quad_fs.material['_Rounding'] = rounding
        self.quad_fs.render()


class ShaderToyFBT(FrameBufferTexture):
    def __init__(self, name, width, height, material: IMaterial, channel=4, ):
        super().__init__(name, width, height, channel, False)
        self.quad_fs = geometry.QuadFullScreen(f"{name}_full_screen_quad", material)

    @record_last_render_time
    def render(self, textures_to_ues: Optional[list[moderngl.Texture]] = None, **kwargs):
        """

        :param textures_to_ues:
        :param kwargs: prog keys must start with "i" or "_";
        :return:
        """
        self.fbo.use()
        self.fbo.clear()
        for key, value in kwargs.items():
            if not key.startswith("i") and not key.startswith("_"):
                logging.warning(f"parameter [{key}] must start with \"i\" or \"_\"")
                continue
            self.quad_fs.material[key] = value

        if textures_to_ues is not None:
            for i, tex in enumerate(textures_to_ues):
                tex.use(i)

        self.quad_fs.render()


class ChartFBT(FrameBufferTexture):
    def __init__(self,
                 width, height,
                 capacity: int = 100,
                 fixed_chart_min=None,
                 fixed_chart_max=None,
                 bg_color=(0, 0, 0, 0),
                 color_min=(0.5, 0.5, 0.5, 0.5),
                 color_max=(1, 1, 1, 1),
                 line_color=(1, 1, 1, 1)
                 ):
        super().__init__(f"chart_{uuid.uuid4()}", width, height, 4, False)
        _mat = MaterialLib.GetDefaultMat_Chart()
        self.quad_fs: geometry.QuadFullScreen = geometry.QuadFullScreen(f"{self.name}_full_screen_quad", _mat)
        self.capacity: int = capacity
        self.data: Optional[np.ndarray] = None
        self.data_tex: SimpleTexture = SimpleTexture(f"~{self.name}_capacity_tex", capacity, 1, 1, dtype="f4")
        self.num_undefined_data = capacity
        self.data_min: float = 0.0  # 数据的真实范围
        self.data_max: float = 0.0
        self._fixed_chart_min: Optional[float] = fixed_chart_min
        self._fixed_chart_max: Optional[float] = fixed_chart_max
        self.chart_min: float = 0.0 if fixed_chart_min is None else fixed_chart_min  # 图表的显示范围
        self.chart_max: float = 1.0 if fixed_chart_max is None else fixed_chart_max
        self.color_min = color_min
        self.color_max = color_max
        self.bg_color = bg_color
        self.line_color = line_color

        self.write_data(np.zeros(shape=(capacity,), dtype=np.float32), num_undefined=capacity)
        self._init_prog()

    def update_size(self, width, height):
        super().update_size(width, height)
        self._on_size_changed()

    def write_data(self, data: np.ndarray, num_undefined=0):
        """整个覆盖"""
        assert isinstance(data, np.ndarray) and len(data.shape) == 1
        if not data.dtype == np.float32:
            logging.warning(f"converting data type from ({data.dtype}) to (np.float32)")
            data = data.astype(np.float32)

        if len(data) != self.capacity:
            logging.warning(f"The length of the data you provided ({len(data)}) does not match self.capacity. "
                            f"Adjusting capacity to accommodate the data length, which may result in some performance loss. "
                            f"Please avoid calling this every frame.")

            self.capacity = len(data)
            self._on_capacity_changed()

        self.data = data
        self.data_tex.texture.write(self.data.tobytes())
        self.num_undefined_data = num_undefined
        self._on_data_changed()

    def push_data(self, data: float):
        # 左移一位
        self.data[0:-1] = self.data[1:]
        self.data[-1] = data
        self.data_tex.texture.write(self.data.tobytes())
        self.num_undefined_data = max(0, self.num_undefined_data - 1)
        self._on_data_changed()

    def _init_prog(self):
        self.quad_fs.material['_Resolution'] = (self.width, self.height)
        self.quad_fs.material['_DataTex'] = 0
        self.quad_fs.material['_Capacity'] = float(self.capacity)
        self.quad_fs.material['_DataMin'] = self.chart_min
        self.quad_fs.material['_DataMax'] = self.chart_max
        self.quad_fs.material['_ColorMin'] = self.color_min
        self.quad_fs.material['_ColorMax'] = self.color_max
        self.quad_fs.material['_ColorLine'] = self.line_color
        self.quad_fs.material['_NumUndefinedData'] = float(self.num_undefined_data)

    def _on_capacity_changed(self):
        _name = self.data_tex.name
        del self.data_tex
        self.data_tex = SimpleTexture(_name, self.capacity, 1, 1, "f4")
        self.quad_fs.material['_Capacity'] = float(self.capacity)

    def _on_data_changed(self):
        if self.num_undefined_data != self.capacity:

            self.data_min = np.min(self.data[self.num_undefined_data:])
            self.data_max = np.max(self.data[self.num_undefined_data:])
        else:
            self.data_min = 0
            self.data_max = 1

        if self._fixed_chart_min is None or self._fixed_chart_max is None:
            min_max_range = self.data_max - self.data_min
            avg = (self.data_min + self.data_max) / 2.0
            min_max_range = 1.0 if min_max_range == 0.0 else min_max_range * 1.5

            self.chart_min = (avg - min_max_range / 2.0) if self._fixed_chart_min is None else self._fixed_chart_min
            self.chart_max = (avg + min_max_range / 2.0) if self._fixed_chart_max is None else self._fixed_chart_max

        self.quad_fs.material['_DataMin'] = self.chart_min
        self.quad_fs.material['_DataMax'] = self.chart_max
        self.quad_fs.material['_NumUndefinedData'] = float(self.num_undefined_data)

    def _on_size_changed(self):
        self.quad_fs.material['_Resolution'] = (self.width, self.height)

    @record_last_render_time
    def render(self):
        self.data_tex.use(0)
        self.fbo.use()
        self.fbo.clear(*self.bg_color)
        self.quad_fs.render()


class ProgressBarFBT(FrameBufferTexture):
    def __init__(self, width, height):
        super().__init__(f"progress_{uuid.uuid4()}", width, height, 4, False)
        _mat = MaterialLib.GetDefaultMat_ProgressBar()
        self.quad_fs: geometry.QuadFullScreen = geometry.QuadFullScreen(f"{self.name}_full_screen_quad", _mat)

    @record_last_render_time
    def render(self, progress, rounding=4, state_value: int = 1):
        """
        values for state, see progress_utils.py for detail
        Prepare = 0
        Running = 1
        Complete = 2
        Error = 3
        NotFound = 4

        :param progress:
        :param rounding:
        :param state_value:
        :return:
        """
        self.fbo.use()
        self.fbo.clear()
        self.quad_fs.material['_T'] = g.mTime
        self.quad_fs.material['_BgColor'] = g.mImguiStyle.colors[imgui.COLOR_FRAME_BACKGROUND]
        self.quad_fs.material['_BarColor'] = g.mImguiStyle.colors[imgui.COLOR_PLOT_HISTOGRAM]
        self.quad_fs.material['_Resolution'] = (self.width, self.height)
        self.quad_fs.material['_Rounding'] = rounding
        self.quad_fs.material['_Progress'] = progress
        self.quad_fs.material['_IsPreparing'] = 1.0 if state_value == 0 else 0.0
        self.quad_fs.material['_IsRunning'] = 1.0 if state_value == 1 else 0.0

        self.quad_fs.render()
