import math
from typing import Optional

import imgui

from gui.components import c
from gui.global_app_state import g
from gui.modules import LayoutModule, ChartModule
from gui.utils import progress_utils as pu
from gui.utils.progress_utils import ProgressState, ProgressContex, _state2str
from gui.windows.base_window import BaseWindow


class BottomBarWindow(BaseWindow):
    LAYOUT_NAME = 'level1_bot'
    _last_fps_update_time = -1
    _fps_count = 0
    _fps_in_last_second = 60
    _record_period = 0.5  # second

    @classmethod
    def w_init(cls):
        super().w_init()

    @classmethod
    def w_update(cls):
        super().w_update()

        cls._fps_count += 1
        if g.mTime - cls._last_fps_update_time > cls._record_period:
            cls._fps_in_last_second = round(cls._fps_count / cls._record_period)
            cls._last_fps_update_time = g.mTime
            cls._fps_count = 0
            ChartModule.push_chart_data("fps", math.sin(g.mTime * 0.1) * 0.5 + 0.5)

    @classmethod
    def w_show(cls, **kwargs):
        super().w_show()

        org_window_padding = g.mImguiStyle.window_padding
        org_frame_padding = g.mImguiStyle.frame_padding
        new_window_padding = (8 * g.global_scale, 4 * g.global_scale)
        new_frame_padding = (8 * g.global_scale, org_frame_padding[1] + org_window_padding[1] - new_window_padding[1])
        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, new_window_padding)
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, new_frame_padding)

        flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
        flags |= imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE

        with LayoutModule.LayoutWindow(cls.LAYOUT_NAME, flags=flags):
            # ==========================================================================
            #                           Window Begin
            # ==========================================================================
            cursor_pos_y_for_text_height_obj = (imgui.get_window_height() - g.font_size) / 2
            # Display Fps
            fps_str = str(cls._fps_in_last_second)
            imgui.set_cursor_pos_y(cursor_pos_y_for_text_height_obj)
            imgui.text(fps_str)

            # Display Progress
            imgui.same_line()
            imgui.set_cursor_pos_x(g.font_size + g.mImguiStyle.item_spacing[0] * 3)
            imgui.set_cursor_pos_y(cursor_pos_y_for_text_height_obj)

            num_active_progress = pu.p_get_num_active_progress()
            ctx: Optional[ProgressContex] = None

            if num_active_progress == 0:
                c.progress_bar("bot_progress", 200 * g.global_scale, g.font_size, progress=0, state_value=ProgressState.NotFound)
            elif num_active_progress == 1:
                ctxs: dict = pu.p_get_all_active_ctx()
                first_key = next(iter(ctxs))
                ctx = ctxs[first_key]
                c.progress_bar("bot_progress", 200 * g.global_scale, g.font_size, progress=ctx.progress, state_value=ctx.state.value)
            else:
                c.progress_bar("bot_progress", 200 * g.global_scale, g.font_size, progress=pu.p_get_mean_progress(), state_value=1)
            if imgui.is_item_clicked(imgui.MOUSE_BUTTON_LEFT):
                from gui.windows import ProgressWindow
                if not ProgressWindow.is_opened():
                    ProgressWindow.w_open()
            imgui.same_line()
            imgui.set_cursor_pos_y(cursor_pos_y_for_text_height_obj)

            if num_active_progress == 0:
                c.gray_text(f"no task running")
            elif num_active_progress == 1:
                c.gray_text(f"[{ctx.display_name}] {_state2str[ctx.state.value]}", False)
            else:
                c.gray_text(f"[Multiple Tasks ({pu.p_get_num_active_progress()})] {_state2str[ProgressState.Running.value]}", False)
            if imgui.is_item_clicked(imgui.MOUSE_BUTTON_LEFT):
                from gui.windows import ProgressWindow
                if not ProgressWindow.is_opened():
                    ProgressWindow.w_open()
            imgui.same_line()
            # progress 测试代码 ===============================================
            # if imgui.button("create test progress"):
            #     pu.p_create_contex("test_progress")
            #     pu.p_new_progress("test_progress", 1000)
            # if pu.p_has_contex("test_progress") and pu.p_get_progress("test_progress") < 1.0:
            #     pu.p_update("test_progress", 1)
            # imgui.same_line()
            # if imgui.button("create test progress2"):
            #     pu.p_create_contex("test_progress2")
            #     pu.p_new_progress("test_progress2", 1000)
            # if pu.p_has_contex("test_progress2") and pu.p_get_progress("test_progress2") < 1.0:
            #     pu.p_update("test_progress2", 1)
            # ================================================================
            imgui.same_line()

            c.move_to_horizontal_right(3)
            imgui.set_cursor_pos_y(new_window_padding[1])
            if c.icon_button("texture", id="texture_viewer", tooltip="Texture Viewer"):
                from gui.windows import TextureViewerWindow
                TextureViewerWindow.w_open()

            imgui.same_line()
            if c.icon_button("charts-bar", id="performance_inspector", tooltip="Performance Inspector"):
                from gui.windows import PerformanceInspectorWindow
                PerformanceInspectorWindow.w_open()
            # ==========================================================================
            #                           Window End
            # ==========================================================================
        imgui.pop_style_var(2)
