from typing import Literal

import imgui

from gui.modules.base_module import BaseModule

DrawListTypes = Literal['window', 'foreground', 'background', 'overlay']


class DrawingModule(BaseModule):
    @classmethod
    def m_init(cls):
        pass

    @classmethod
    def get_draw_list(cls, draw_list_type: DrawListTypes):
        if draw_list_type == 'window':
            return imgui.get_window_draw_list()
        elif draw_list_type == 'foreground':
            return imgui.get_foreground_draw_list()
        elif draw_list_type == 'background':
            return imgui.get_background_draw_list()
        elif draw_list_type == 'overlay':
            return imgui.get_overlay_draw_list()

    @classmethod
    def draw_circle(cls, centre_x, centre_y, radius, col, num_segments=0, thickness=1.0,
                    draw_list_type: DrawListTypes = 'window'):
        draw_list = cls.get_draw_list(draw_list_type)
        draw_list.add_circle(centre_x, centre_y, radius, imgui.get_color_u32_rgba(*col),
                             num_segments=num_segments, thickness=thickness)

    @classmethod
    def draw_circle_filled(cls, centre_x, centre_y, radius, col, num_segments=0,
                           draw_list_type: DrawListTypes = 'window'):
        draw_list = cls.get_draw_list(draw_list_type)
        draw_list.add_circle_filled(centre_x, centre_y, radius, imgui.get_color_u32_rgba(*col),
                                    num_segments=num_segments)

    @classmethod
    def draw_rect(cls, upper_left_x, upper_left_y, lower_right_x,
                  lower_right_y, col, rounding=0.0, flags=0, thickness=1.0, draw_list_type: DrawListTypes = 'window'):
        draw_list = cls.get_draw_list(draw_list_type)
        draw_list.add_rect(upper_left_x, upper_left_y, lower_right_x, lower_right_y, imgui.get_color_u32_rgba(*col),
                           rounding=rounding, flags=flags, thickness=thickness)

    @classmethod
    def draw_rect_filled(cls, upper_left_x, upper_left_y, lower_right_x,
                         lower_right_y, col, rounding=0.0, flags=0, draw_list_type: DrawListTypes = 'window'):
        draw_list = cls.get_draw_list(draw_list_type)
        draw_list.add_rect_filled(upper_left_x, upper_left_y, lower_right_x, lower_right_y,
                                  imgui.get_color_u32_rgba(*col), rounding=rounding, flags=flags)

    @classmethod
    def draw_image(cls, texture_id, upper_left_x, upper_left_y, lower_right_x,
                         lower_right_y, uv_a=(0, 0), uv_b=(1, 1), col=(1, 1, 1, 1),
                   draw_list_type: DrawListTypes = 'window'):
        draw_list = cls.get_draw_list(draw_list_type)
        draw_list.add_image(texture_id, (upper_left_x, upper_left_y), (lower_right_x, lower_right_y), uv_a, uv_b, imgui.get_color_u32_rgba(*col))
