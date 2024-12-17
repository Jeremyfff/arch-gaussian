import imgui

from gui.contents import NodeEditorContent
from gui.windows.base_window import BaseWindow


class NodeEditorWindow(BaseWindow):

    @classmethod
    def w_init(cls):
        super().w_init()

    @classmethod
    def w_update(cls):
        super().w_update()

    @classmethod
    def w_show(cls, **kwargs):
        super().w_show()
        # begin window
        flags = imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE
        imgui.begin('My Node Editor Window', True, flags)
        NodeEditorContent.c_show()
        imgui.end()  # end window
