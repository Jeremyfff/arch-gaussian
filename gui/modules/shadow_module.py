import os

import imgui
import numpy as np
from PIL import Image

from gui import components as c
from gui import global_var as g
from gui.modules.base_module import BaseModule


class ShadowModule(BaseModule):
    _rect_min_list: list[np.ndarray] = []  # 记录每个popup窗口的左上角坐标
    _rect_max_list: list[np.ndarray] = []  # 记录每个popup窗口的右下角坐标
    _active_list: list[bool] = []  # 记录每个popup窗口是否被focus
    _upper_left_offset = np.array([20, 20])
    _lower_right_offset = np.array([40, 40])

    _mid_uv0 = 0.4
    _mid_uv1 = 0.6
    _shadow_active_color = (0, 0, 0, 0.3)
    _shadow_inactive_color = (0, 0, 0, 0.15)

    _shadow_texture = None
    _popup_window_class = None
    _drawing_module = None
    _texture_module = None

    @classmethod
    def m_init(cls):
        super().m_init()
        from gui.modules import texture_module
        cls._texture_module = texture_module
        from gui.modules import DrawingModule
        cls._drawing_module = DrawingModule
        from gui.windows.base_window import PopupWindow
        cls._popup_window_class = PopupWindow
        shadow_img_path = os.path.join(g.GUI_RESOURCES_ROOT, f'textures/shadow.png')
        shadow_img = Image.open(shadow_img_path)
        cls._shadow_texture = cls._texture_module.create_texture_from_image(shadow_img)

    @classmethod
    def update_window_rects(cls, windows):
        """windows show be list of popup windows"""
        cls._rect_min_list.clear()
        cls._rect_max_list.clear()
        cls._active_list.clear()
        for window in windows:
            # assert window.__base__ == cls._popup_window_class, \
            #     f'[{window.__name__}] window must be instance of {cls._popup_window_class.__name__}'
            if not window.is_opened():
                continue
            cls._rect_min_list.append(np.array(window.get_rect_min()))
            cls._rect_max_list.append(np.array(window.get_rect_max()))
            cls._active_list.append(window.is_active())
            return

    @classmethod
    def draw_shadows(cls):
        if len(cls._rect_min_list) == 0:
            return
        imgui.set_cursor_pos((0, 0))
        c.begin_child('shadow_child', 0, 0, flags=imgui.WINDOW_NO_INPUTS | imgui.WINDOW_NO_NAV)
        for i in range(len(cls._rect_min_list)):
            r_min = cls._rect_min_list[i]  # rect min
            r_max = cls._rect_max_list[i]  # shadow max
            s_min = r_min - cls._upper_left_offset  # shadow min
            s_max = r_max + cls._lower_right_offset  # shadow max
            color = cls._shadow_active_color if cls._active_list[i] else cls._shadow_inactive_color
            uv_0 = cls._mid_uv0
            uv_1 = cls._mid_uv1
            layer = 'window'
            # middle
            cls._drawing_module.draw_image(cls._shadow_texture.glo,
                                           *r_min, *r_max, (uv_0, uv_0), (uv_1, uv_1), color, layer)
            # upper left
            cls._drawing_module.draw_image(cls._shadow_texture.glo,
                                           *s_min, *r_min, (0.00, 0.00), (uv_0, uv_0), color, layer)
            # lower_right
            cls._drawing_module.draw_image(cls._shadow_texture.glo,
                                           *r_max, *s_max, (uv_1, uv_1), (1.00, 1.00), color, layer)

            # upper right
            cls._drawing_module.draw_image(cls._shadow_texture.glo,
                                           r_max[0], s_min[1], s_max[0], r_min[1], (uv_1, 0.00), (1.00, uv_0), color,
                                           layer)
            # lower left
            cls._drawing_module.draw_image(cls._shadow_texture.glo,
                                           s_min[0], r_max[1], r_min[0], s_max[1], (0.00, uv_1), (uv_0, 1.00), color,
                                           layer)
            # up
            cls._drawing_module.draw_image(cls._shadow_texture.glo,
                                           r_min[0], s_min[1], r_max[0], r_min[1], (uv_0, 0.00), (uv_1, uv_0), color,
                                           layer)
            # right
            cls._drawing_module.draw_image(cls._shadow_texture.glo,
                                           r_max[0], r_min[1], s_max[0], r_max[1], (uv_1, uv_0), (1.00, uv_1), color,
                                           layer)
            # down
            cls._drawing_module.draw_image(cls._shadow_texture.glo,
                                           r_min[0], r_max[1], r_max[0], s_max[1], (uv_0, uv_1), (uv_1, 1.00), color,
                                           layer)
            # left
            cls._drawing_module.draw_image(cls._shadow_texture.glo,
                                           s_min[0], r_min[1], r_min[0], r_max[1], (0.00, uv_0), (uv_0, uv_1), color,
                                           layer)

        imgui.end_child()
