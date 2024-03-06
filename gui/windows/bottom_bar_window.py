import imgui

from gui import global_var as g
from gui.modules import LayoutModule
from gui.windows.base_window import BaseWindow


class BottomBarWindow(BaseWindow):
    LAYOUT_NAME = 'level1_bot'

    @classmethod
    def w_init(cls):
        super().w_init()

    @classmethod
    def w_update(cls):
        super().w_update()

    @classmethod
    def w_show(cls):
        super().w_show()
        with LayoutModule.LayoutWindow(cls.LAYOUT_NAME):
            fps = int(1.0 / g.mFrametime)
            imgui.text(str(fps))

