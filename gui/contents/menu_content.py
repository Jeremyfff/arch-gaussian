import imgui

from gui.components import c
from gui.contents.base_content import BaseContent


class MainMenuContent(BaseContent):
    @classmethod
    def c_init(cls):
        super().c_init()

    @classmethod
    def c_update(cls):
        super().c_update()

    @classmethod
    def c_show(cls):
        super().c_show()
        if imgui.begin_menu('File').opened:
            c.quick_menu_item('Open File', lambda: print(f'open file'))
            c.quick_menu_item('New File', lambda: print('new file'))
            c.quick_menu_item('Exit')
            imgui.end_menu()
        if imgui.begin_menu('Process').opened:
            c.quick_menu_item('Process1')
            c.quick_menu_item('Process2')
            c.quick_menu_item('Process3')
            imgui.end_menu()
        if imgui.begin_menu('Train').opened:
            c.quick_menu_item('train guide')
            imgui.end_menu()

    @classmethod
    def c_on_show(cls):
        super().c_on_show()

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()

