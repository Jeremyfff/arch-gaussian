import imgui

from gui import global_var as g


LAYOUT_NAME = 'level1_bot'


def show():
    imgui.set_next_window_size(*g.mLayoutScheme.get_size(LAYOUT_NAME))
    imgui.set_next_window_position(*g.mLayoutScheme.get_pos(LAYOUT_NAME))
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_MENU_BAR | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
    imgui.begin('bottom_bar_window', flags=flags)
    imgui.end()
