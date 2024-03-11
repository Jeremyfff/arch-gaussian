from typing import Optional

import imgui
import numpy as np

from gui import global_var as g
from gui.contents.base_content import BaseContent
from gui.modules import CursorModule
from gui.modules import DrawingModule
from gui.modules import EventModule
from gui.modules import LayoutModule
from gui.modules import StyleModule


class VerticalResizeHandleContent(BaseContent):
    cursor_region: Optional[CursorModule.CursorRegion] = None
    is_in_cursor_region = False
    can_drag = False
    NORMAL_HANDLE_COLOR = (0, 0, 0, 0)
    HIGHLIGHTED_HANDLE_COLOR = StyleModule.COLOR_PRIMARY
    REGION_OFFSET = np.array([2, 0])  # 检测hover时的扩展范围

    @classmethod
    def c_init(cls):
        super().c_init()
        cls.cursor_region = CursorModule.CursorRegion(CursorModule.CursorType.CURSOR_SIZE_RIGHT)

    @classmethod
    def c_update(cls):
        super().c_update()

    @classmethod
    def c_show(cls):
        super().c_show()
        window_pos = np.array(imgui.get_window_position())
        window_size = np.array(imgui.get_window_size())

        region_min = window_pos
        region_max = window_pos + window_size
        DrawingModule.draw_rect_filled(
            region_min[0], region_min[1],
            region_max[0], region_max[1],
            cls.HIGHLIGHTED_HANDLE_COLOR if cls.is_in_cursor_region else cls.NORMAL_HANDLE_COLOR,
            draw_list_type='foreground'
        )
        _, cls.is_in_cursor_region = cls.cursor_region.update(
            region_min - cls.REGION_OFFSET, region_max + cls.REGION_OFFSET)

    @classmethod
    def c_on_show(cls):
        super().c_on_show()
        EventModule.register_mouse_press_callback(cls.on_mouse_press)
        EventModule.register_mouse_release_callback(cls.on_mouse_release)
        EventModule.register_mouse_drag_callback(cls.on_mouse_drag)

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()
        EventModule.unregister_mouse_press_callback(cls.on_mouse_press)
        EventModule.unregister_mouse_release_callback(cls.on_mouse_release)
        EventModule.unregister_mouse_drag_callback(cls.on_mouse_drag)

    @classmethod
    def on_mouse_press(cls, x: int, y: int, button: int):
        _ = x, y, button
        if not cls.is_in_cursor_region:
            return
        cls.can_drag = True

    @classmethod
    def on_mouse_release(cls, x: int, y: int, button: int):
        _ = x, y, button
        if cls.can_drag:
            cls.can_drag = False
            EventModule.resize(*g.mWindowEvent.window_size)  # 触发resize

    @classmethod
    def on_mouse_drag(cls, x: int, y: int, dx: int, dy: int):
        _ = x, y, dy
        if not cls.can_drag:
            return
        resizable_layout = LayoutModule.vertical_resizable_layout
        resizable_layout.set_width(resizable_layout.get_width() + dx)
        LayoutModule.layout.update()
