from typing import Callable
import imgui
from ImNodeEditor import NE, Node

from gui import global_var as g
from gui import main_window
from gui import node_editor_window
from gui import top_bar_window
from gui import bottom_bar_window
from gui import nav_bar_window

from gui.modules import layout_module, graphic_module, style_module, texture_module


def start():
    style_module.init()  # first init style
    layout_module.init()
    texture_module.init()


def update():
    """logical update"""
    Node.main_loop()


def render_ui():
    """ui update"""
    imgui.show_demo_window()
    top_bar_window.show()
    bottom_bar_window.show()
    nav_bar_window.show()
    main_window.show()


def resize(width: int, height: int):
    layout_module.on_resize()


def key_event(key, action, modifiers):
    NE.handle_key_event(key, action, modifiers)


def mouse_position_event(x, y, dx, dy):
    NE.handle_mouse_position_event(x, y, dx, dy)


def mouse_drag_event(x, y, dx, dy):
    NE.handle_mouse_drag_event(x, y, dx, dy)


def mouse_scroll_event_smooth(x_offset, y_offset):
    pass


def mouse_scroll_event(x_offset, y_offset):
    NE.handle_mouse_scroll_event(x_offset, y_offset)


def mouse_press_event(x, y, button):
    NE.handle_mouse_press_event(x, y, button)


def mouse_release_event(x: int, y: int, button: int):
    NE.handle_mouse_release_event(x, y, button)


def unicode_char_entered(char):
    pass
