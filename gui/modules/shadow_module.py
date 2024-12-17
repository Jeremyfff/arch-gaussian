import os
from typing import Optional, Type

import imgui
import numpy as np
from PIL import Image

from gui.components import c
from gui.global_app_state import g
from gui.modules.base_module import BaseModule
from gui.global_info import *

__runtime__ = True
if not __runtime__:
    # for type hint
    from gui.modules import TextureModule
    from gui.modules import DrawingModule, DrawListTypes
    from gui.windows.base_window import PopupWindow

    raise Exception("this code will never be reached")


class ShadowModule(BaseModule):
    _has_active_window: bool = False  # 是否有window处于active
    _rect_min: tuple[int, int] = (0, 0)  # 记录popup窗口的左上角坐标
    _rect_max: tuple[int, int] = (0, 0)  # 记录popup窗口的右下角坐标

    _upper_left_offset = (20, 20)
    _lower_right_offset = (40, 40)

    _mid_uv0 = 0.4
    _mid_uv1 = 0.6
    _shadow_active_color = (0, 0, 0, 0.3)

    _popup_window_class: Type["PopupWindow"] = None
    _drawing_module: Type["DrawingModule"] = None
    _texture_module: Type["TextureModule"] = None
    _all_popup_windows: list[Type["PopupWindow"]] = []

    @classmethod
    def m_init(cls):
        super().m_init()
        from gui.modules import TextureModule
        cls._texture_module = TextureModule
        from gui.modules import DrawingModule
        cls._drawing_module = DrawingModule
        from gui.windows.base_window import PopupWindow
        cls._popup_window_class = PopupWindow
        from gui.windows import POPUP_WINDOWS
        cls._all_popup_windows = POPUP_WINDOWS

    @classmethod
    def m_render(cls):
        cls._update_window_rects()
        cls._draw_shadows()

    @classmethod
    def _update_window_rects(cls):
        """windows show be list of popup windows"""
        cls._has_active_window = False
        for window in cls._all_popup_windows:
            if not window.is_opened():
                continue
            if not window.is_active():
                continue
            cls._rect_min = window.get_rect_min()
            cls._rect_max = window.get_rect_max()
            cls._has_active_window = True
            return

    @classmethod
    def _draw_shadows(cls):
        if not cls._has_active_window:
            return
        # imgui.set_cursor_pos((0, 0))
        # c.begin_child('shadow_child', 0, 0, flags=imgui.WINDOW_NO_INPUTS | imgui.WINDOW_NO_NAV)
        r_min = cls._rect_min  # rect min
        r_max = cls._rect_max  # rect max
        s_min = (r_min[0] - cls._upper_left_offset[0], r_min[1] - cls._upper_left_offset[1])  # shadow min
        s_max = (r_max[0] + cls._lower_right_offset[0], r_max[1] + cls._lower_right_offset[1])  # shadow max
        color = cls._shadow_active_color
        uv_0 = cls._mid_uv0
        uv_1 = cls._mid_uv1
        layer: DrawListTypes = 'overlay'
        shadow_tex_id = cls._texture_module.get_texture_glo("shadow")
        # middle
        # cls._drawing_module.draw_image(cls._shadow_texture.glo,
        #                                *r_min, *r_max, (uv_0, uv_0), (uv_1, uv_1), color, layer)
        # upper left
        cls._drawing_module.draw_image(shadow_tex_id,
                                       *s_min, *r_min, (0.00, 0.00), (uv_0, uv_0), color, layer)
        # lower_right
        cls._drawing_module.draw_image(shadow_tex_id,
                                       *r_max, *s_max, (uv_1, uv_1), (1.00, 1.00), color, layer)

        # upper right
        cls._drawing_module.draw_image(shadow_tex_id,
                                       r_max[0], s_min[1], s_max[0], r_min[1], (uv_1, 0.00), (1.00, uv_0), color,
                                       layer)
        # lower left
        cls._drawing_module.draw_image(shadow_tex_id,
                                       s_min[0], r_max[1], r_min[0], s_max[1], (0.00, uv_1), (uv_0, 1.00), color,
                                       layer)
        # up
        cls._drawing_module.draw_image(shadow_tex_id,
                                       r_min[0], s_min[1], r_max[0], r_min[1], (uv_0, 0.00), (uv_1, uv_0), color,
                                       layer)
        # right
        cls._drawing_module.draw_image(shadow_tex_id,
                                       r_max[0], r_min[1], s_max[0], r_max[1], (uv_1, uv_0), (1.00, uv_1), color,
                                       layer)
        # down
        cls._drawing_module.draw_image(shadow_tex_id,
                                       r_min[0], r_max[1], r_max[0], s_max[1], (uv_0, uv_1), (uv_1, 1.00), color,
                                       layer)
        # left
        cls._drawing_module.draw_image(shadow_tex_id,
                                       s_min[0], r_min[1], r_min[0], r_max[1], (0.00, uv_0), (uv_0, uv_1), color,
                                       layer)

        # imgui.end_child()
