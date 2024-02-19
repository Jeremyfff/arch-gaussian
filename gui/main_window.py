import imgui

import gui.global_var as g
from gui.modules import graphic_module
from gui.contents import prepare_content, train_3dgs_content, edit_3dgs_content, \
    viewer_content, node_editor_content, blank_content

LAYOUT_NAME = 'level2_right'


def show():
    if g.mCurrNavIdx == 0:
        show_split_page(prepare_content, node_editor_content)
    elif g.mCurrNavIdx == 1:
        show_split_page(train_3dgs_content, viewer_content)
    elif g.mCurrNavIdx == 2:
        show_split_page(edit_3dgs_content, viewer_content)
    else:
        show_one_page(blank_content)


def show_one_page(content):
    imgui.set_next_window_size(*g.mLayoutScheme.get_size(LAYOUT_NAME))
    imgui.set_next_window_position(*g.mLayoutScheme.get_pos(LAYOUT_NAME))
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
    imgui.begin('level2_right', flags=flags)
    content.show()
    imgui.end()


def show_split_page(content1, content2):
    imgui.set_next_window_size(*g.mLayoutScheme.get_size('level3_left'))
    imgui.set_next_window_position(*g.mLayoutScheme.get_pos('level3_left'))
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
    imgui.begin('level3_left', flags=flags)
    content1.show()
    imgui.end()

    imgui.set_next_window_size(*g.mLayoutScheme.get_size('level3_right'))
    imgui.set_next_window_position(*g.mLayoutScheme.get_pos('level3_right'))
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
    imgui.begin('level3_right', flags=flags)
    content2.show()
    imgui.end()
