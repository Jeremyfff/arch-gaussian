import logging
import os
from abc import abstractmethod
from typing import Optional

import imgui
import moderngl

import gui.windows  # avoid circulate import
from gui.global_app_state import g
from gui.global_info import TRANSLATION_FOLDER
from gui.modules import DrawingModule, LanguageModule
from gui.modules.language_module import LanguageSet


class BaseWindow:
    TRANSLATION_FILE_NAME: str = None  # 用户设置项
    _l: LanguageSet = None

    _inited = False

    @classmethod
    @abstractmethod
    def w_init(cls):
        logging.info(f'[{cls.__name__}] init')

        if cls.TRANSLATION_FILE_NAME is None:
            logging.warning(f"There is no translation file for [{cls.__name__}]. To specify a translation file, go to [{TRANSLATION_FOLDER}] to add a translation csv file and specify the _translation_file_name property of the class.")
            cls._l = LanguageSet()  # we use an empty language set
        else:
            path = os.path.join(TRANSLATION_FOLDER, cls.TRANSLATION_FILE_NAME)
            try:
                cls._l = LanguageModule.load_language_set(path)
            except Exception as e:
                logging.error(f"[{cls.__name__}] Error loading language set at {path}. {e}")
                cls._l = LanguageSet()

        cls._inited = True

    @classmethod
    @abstractmethod
    def w_update(cls):
        # if not cls._inited:
        #     cls.w_init()  # late init
        pass

    @classmethod
    @abstractmethod
    def w_show(cls, **kwargs):
        # if not cls._inited:
        #     cls.w_init()  # late init
        pass


class PopupWindow(BaseWindow):
    _opened = False  # 是否打开
    _active = False  # 是否具有焦点
    _position = (0, 0)  # 当不为-1时，将作为初始位置
    _size = (0, 0)  # 当不为-1时，将作为初始尺寸
    _name = ''
    _flags = imgui.WINDOW_NONE

    # 延迟出现
    _popup_delay_frames = 0  # 延迟出现的帧数
    _accumulated_frames = 0  # Variable to store the accumulated frame count
    _step_size = 0  # Variable to store the increment for each accumulation

    # 焦点处理
    _last_active = False

    # 背景模糊
    _bg_alpha = 0
    _bg_tex: Optional[moderngl.Texture] = None
    _bg_blur_last_update_time = -1

    @classmethod
    @abstractmethod
    def w_init(cls):
        super().w_init()
        cls._name = cls.__name__ if cls._name == '' else cls._name

        if cls._position[0] != -1 and cls._position[1] != -1:
            imgui.set_next_window_position(*cls._position)

        if cls._size[0] != -1 and cls._size[1] != -1:
            imgui.set_next_window_size(*cls._size)

    @classmethod
    @abstractmethod
    def w_update(cls):
        cls._accumulated_frames += cls._step_size
        if cls._accumulated_frames > 1:
            cls._opened = True
            cls._accumulated_frames = 0
            cls._step_size = 0

    @classmethod
    def w_show(cls, **kwargs):
        """no need to implement"""
        if not cls._opened:
            return
        super().w_show()

        if "flags" in kwargs.keys():
            flags = kwargs["flags"]
        else:
            flags = cls._flags

        # before window begin
        cls.w_before_window_begin()
        expanded, opened = imgui.begin(cls._name, True, flags)
        # ==================================================================
        #                           window started
        # ==================================================================
        # update variables
        cls._position = imgui.get_window_position()
        cls._size = imgui.get_window_size()

        cls._active = imgui.is_window_focused(imgui.HOVERED_ALLOW_WHEN_BLOCKED_BY_POPUP | imgui.HOVERED_ROOT_AND_CHILD_WINDOWS)

        # show blurred bg if needed
        cls._show_blurred_bg()

        # show main content
        cls.w_content()
        # ==================================================================
        #                             window end
        # ==================================================================
        imgui.end()

        # after window end
        cls.w_after_window_end()

        # handle close
        if not opened:
            cls.w_close()
            return
        # handle refocus
        if not cls._last_active and cls._active:
            cls.on_refocus()
        cls._last_active = cls._active

    @classmethod
    @abstractmethod
    def w_open(cls):
        logging.info(f"[{cls.__name__}] w_open, request blurred bg")
        cls._step_size = 1  # set _step_size 1 to accumulate frames
        cls._last_active = True  # set True to avoid trigger cls.on_refocus()
        cls._request_blurred_bg()  # try to request blurred bg

        # EventModule.register_mouse_scroll_smooth_callback(cls._on_mouse_scroll_smooth)
        # EventModule.register_mouse_drag_callback(cls._on_mouse_drag)

    @classmethod
    @abstractmethod
    def w_close(cls):
        cls._opened = False
        cls._bg_alpha = 0.0

        # EventModule.unregister_mouse_scroll_smooth_callback(cls._on_mouse_scroll_smooth)
        # EventModule.unregister_mouse_drag_callback(cls._on_mouse_drag)

    @classmethod
    def w_before_window_begin(cls):
        pass

    @classmethod
    @abstractmethod
    def w_content(cls):
        pass

    @classmethod
    def w_after_window_end(cls):
        pass

    @classmethod
    def is_opened(cls):
        return cls._opened

    @classmethod
    def is_active(cls):
        return cls._active

    @classmethod
    def get_rect_min(cls) -> tuple[int, int]:
        return cls._position

    @classmethod
    def get_rect_max(cls) -> tuple[int, int]:
        return cls._position[0] + cls._size[0], cls._position[1] + cls._size[1]

    @classmethod
    def on_refocus(cls):
        """当重新获得焦点时"""
        logging.info(f"[{cls.__name__}] on_refocus, request blurred bg")
        cls._request_blurred_bg()

    @classmethod
    def _request_blurred_bg(cls):
        """请求渲染背景模糊图像"""
        if g.mTime - cls._bg_blur_last_update_time < 1.0 / 30.0:
            return
        g.mWindowManager.request_blurred_bg(
            caller=cls,
            exclude_type=gui.windows.ExcludeTypes.Self,
            callback=cls._on_blurred_bg_complete
        )
        cls._bg_blur_last_update_time = g.mTime

    @classmethod
    def _on_blurred_bg_complete(cls, tex: moderngl.Texture):
        """当请求背景图像完成时"""
        cls._bg_tex = tex
        cls._bg_blur_last_update_time = g.mTime

    @classmethod
    def _show_blurred_bg(cls):
        if not cls._active:
            cls._bg_alpha -= 2.5 * g.mFrametime
            cls._bg_alpha = max(0.0, cls._bg_alpha)
        else:
            cls._bg_alpha += 2.5 * g.mFrametime
            cls._bg_alpha = min(1.0, cls._bg_alpha)

        if cls._bg_tex is None:
            return
        if cls._bg_alpha == 0:
            return

        start = imgui.get_window_position()
        size = imgui.get_window_size()
        end = (start[0] + size[0],
               start[1] + size[1])
        start_uv = (start[0] / g.mWindowSize[0], 1 - start[1] / g.mWindowSize[1])
        end_uv = (end[0] / g.mWindowSize[0], 1 - end[1] / g.mWindowSize[1])
        DrawingModule.draw_image(cls._bg_tex.glo, *start, *end, start_uv, end_uv, draw_list_type="window", col=(1, 1, 1, 0.5 * cls._bg_alpha))

    @classmethod
    def get_size(cls):
        return cls._size

    @classmethod
    def get_position(cls):
        return cls._position

    # @classmethod
    # def _on_mouse_scroll_smooth(cls, x, y):
    #     if abs(y) > 0.01:
    #         cls._request_blurred_bg()
    #
    # @classmethod
    # def _on_mouse_drag(cls, x, y, z, w):
    #     cls._request_blurred_bg()
