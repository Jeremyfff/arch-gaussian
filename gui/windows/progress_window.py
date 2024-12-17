# from gui.contents import
import imgui

from gui.global_app_state import g
from gui.components import c
from gui.modules import LayoutModule, EventModule
from gui.utils import progress_utils as pu
from gui.windows.base_window import PopupWindow


class ProgressWindow(PopupWindow):
    _name = 'ProgressWindow'
    _flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE

    _hide_complete_ctx = False
    _cached_ctx = set()

    @classmethod
    def w_init(cls):
        super().w_init()

    @classmethod
    def w_update(cls):
        super().w_update()

    @classmethod
    def w_content(cls):
        imgui.push_style_var(imgui.STYLE_ITEM_SPACING, (g.mImguiStyle.item_spacing[0], g.mImguiStyle.item_spacing[1] * 2))
        child_height = cls._size[1] - imgui.get_frame_height_with_spacing() - imgui.get_frame_height()
        if len(cls._cached_ctx) == 0:
            # when no task running
            imgui.set_cursor_pos_y(child_height / 2)
            c.gray_text("No Running Tasks", True)
        else:
            # when task running
            c.begin_child("progress_region_child", width=0, height=child_height, border=True)
            for ctx in cls._cached_ctx:
                ctx: pu.ProgressContex = ctx
                imgui.dummy(0, imgui.get_frame_height() / 16)
                ctx.draw_progress_bar(suffix="progress_wnd")  # 在progress window中绘制的进度条，统一添加progress_wnd 后缀
                ctx.draw_text()
                imgui.separator()
                imgui.dummy(0, imgui.get_frame_height() / 8)
            imgui.end_child()

        # hide complete button
        imgui.set_cursor_pos_y(cls._size[1] - imgui.get_frame_height_with_spacing())
        clicked, cls._hide_complete_ctx = imgui.checkbox("Hide Complete", cls._hide_complete_ctx)
        imgui.pop_style_var(1)
        if clicked:
            cls._on_settings_changed()
        # close window
        if imgui.is_mouse_clicked() and not imgui.is_mouse_hovering_rect(*cls.get_rect_min(), *cls.get_rect_max()):
            cls.w_close()

    @classmethod
    def w_open(cls):
        super().w_open()
        cls._scan_ctx()
        EventModule.register_progress_ctx_change_callback(cls._on_ctx_changed)

    @classmethod
    def w_close(cls):
        super().w_close()
        EventModule.unregister_progress_ctx_change_callback(cls._on_ctx_changed)

    @classmethod
    def w_before_window_begin(cls):
        bot_pos = LayoutModule.layout.get_pos('level1_bot')
        nav_size = LayoutModule.layout.get_size('level2_left')

        window_width = 400 * g.global_scale
        window_height = 400 * g.global_scale
        imgui.set_next_window_position(nav_size[0], bot_pos[1] - window_height)
        imgui.set_next_window_size(window_width, window_height)
        imgui.set_next_window_focus()

    @classmethod
    def _scan_ctx(cls):
        cls._cached_ctx.clear()

        ctx_dict: dict[str: pu.ProgressContex] = pu.p_get_all_ctx()
        for name, ctx in ctx_dict.items():
            if cls._hide_complete_ctx and ctx.state == pu.ProgressState.Complete:
                continue
            cls._cached_ctx.add(ctx)

    @classmethod
    def _on_settings_changed(cls):
        cls._scan_ctx()

    @classmethod
    def _on_ctx_changed(cls):
        cls._scan_ctx()
