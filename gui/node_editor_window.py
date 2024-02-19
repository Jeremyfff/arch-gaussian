import imgui

from gui.contents import node_editor_content


def show():
    # begin window
    flags = imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE
    imgui.begin('My Node Editor Window', flags=flags)
    node_editor_content.show()
    imgui.end()  # end window
