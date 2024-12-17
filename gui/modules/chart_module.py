import logging
from typing import Type

import imgui

from gui.global_app_state import g
from gui.modules.base_module import BaseModule

__runtime__ = True
if not __runtime__:
    from gui.modules.graphic_module import ChartFBT
    from gui.modules.drawing_module import DrawingModule
    from gui.modules.style_module import StyleModule

class ChartModule(BaseModule):
    _charts: dict[str: "ChartFBT"] = {}

    _drawing_module: Type["DrawingModule"] = None

    @classmethod
    def m_init(cls):
        super().m_init()
        from gui.modules import DrawingModule
        cls._drawing_module = DrawingModule
        from gui.modules import StyleModule
        from gui.utils import color_utils
        color_min = color_utils.set_alpha(color_utils.darken_color(StyleModule.COLOR_PRIMARY, 0.2), 0.8)
        color_max = color_utils.set_alpha(color_utils.lighten_color(StyleModule.COLOR_PRIMARY, 0.1), 1.0)
        line_color = StyleModule.COLOR_PRIMARY
        bg_color = (0, 0, 0, 0.1)
        cls._create_chart("fps", 400, 200, 20, fixed_chart_min=0, color_min=color_min, color_max=color_max, line_color=line_color, bg_color=bg_color)
        cls._create_chart("cpu", 400, 200, 60, fixed_chart_min=0, fixed_chart_max=100, color_min=color_min, color_max=color_max, line_color=line_color, bg_color=bg_color)
        cls._create_chart("gpu", 400, 200, 60, fixed_chart_min=0, fixed_chart_max=100, color_min=color_min, color_max=color_max, line_color=line_color, bg_color=bg_color)
        cls._create_chart("memory", 400, 200, 60, fixed_chart_min=0, color_min=color_min, color_max=color_max, line_color=line_color, bg_color=bg_color)

    @classmethod
    def _create_chart(cls, name, width=400, height=200, capacity=60, fixed_chart_min=None, fixed_chart_max=None, color_min=(0.5, 0.5, 0.5, 0.5), color_max=(1.0, 1.0,1.0,1.0), line_color=(1.0, 1.0, 1.0, 1.0), bg_color=(0, 0, 0, 0)):
        from gui.modules.graphic_module import ChartFBT
        cls._charts[name] = ChartFBT(width, height, capacity, fixed_chart_min=fixed_chart_min, fixed_chart_max=fixed_chart_max, color_min=color_min, color_max=color_max, line_color=line_color, bg_color=bg_color)

    @classmethod
    def push_chart_data(cls, chart_name, data):
        chart: "ChartFBT" = cls._charts[chart_name]
        chart.push_data(data)

    @classmethod
    def write_chart_data(cls, chart_name, data):
        chart: "ChartFBT" = cls._charts[chart_name]
        chart.write_data(data)

    @classmethod
    def draw_chart(cls, chart_name):
        chart: "ChartFBT" = cls._charts[chart_name]

        chart.render()

        imgui.dummy(imgui.get_content_region_available_width(), imgui.get_frame_height() / 2.0)

        window_start = imgui.get_window_position()
        cursor_pos = imgui.get_cursor_pos()
        scroll_y = imgui.get_scroll_y()
        img_start = (window_start[0] + cursor_pos[0] + scroll_y, window_start[1] + cursor_pos[1] + scroll_y)
        width, height = chart.width, chart.height

        imgui.image(chart.texture_id, width, height)

        uv_min = 1 - (chart.data_min - chart.chart_min) / (chart.chart_max - chart.chart_min)
        uv_max = 1 - (chart.data_max - chart.chart_min) / (chart.chart_max - chart.chart_min)
        uv_zero = 1 - (0 - chart.chart_min) / (chart.chart_max - chart.chart_min)

        x_start = img_start[0]
        x_end = img_start[0] + width
        y_min = img_start[1] + uv_min * height
        y_max = img_start[1] + uv_max * height
        y_zero = img_start[1] + uv_zero * height

        cls._drawing_module.draw_line(
            start_x=x_start,
            start_y=y_min,
            end_x=x_end,
            end_y=y_min,
            col=(1, 1, 1, 1),
            draw_list_type="window")

        cls._drawing_module.draw_line(
            start_x=x_start,
            start_y=y_max,
            end_x=x_end,
            end_y=y_max,
            col=(1, 1, 1, 1),
            draw_list_type="window")

        draw_zero_line = abs(uv_zero - uv_min) > 0.1

        if draw_zero_line:
            cls._drawing_module.draw_line(
                start_x=x_start,
                start_y=y_zero,
                end_x=x_end,
                end_y=y_zero,
                col=(1, 1, 1, 0.5),
                draw_list_type="window")

        offset = 8 * g.global_scale if abs(y_max - y_min) < 16 * g.global_scale else 0

        cls._drawing_module.draw_text(
            pos_x=x_end,
            pos_y=y_min - 8 * g.global_scale + offset,
            col=(1, 1, 1, 1),
            text="%.2f" % chart.data_min,
            draw_list_type="window"
        )

        cls._drawing_module.draw_text(
            pos_x=x_end,
            pos_y=y_max - 8 * g.global_scale - offset,
            col=(1, 1, 1, 1),
            text="%.2f" % chart.data_max,
            draw_list_type="window"
        )
        if draw_zero_line:
            cls._drawing_module.draw_text(
                pos_x=x_end,
                pos_y=y_zero,
                col=(1, 1, 1, 0.5),
                text="0.00",
                draw_list_type="window"
            )
        imgui.dummy(imgui.get_content_region_available_width(), imgui.get_frame_height() / 2.0)
