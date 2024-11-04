import imgui

from gui import components as c
from gui import global_var as g
from gui.contents import UserSettingsContent, ProjectSettingsContent, ImguiSettingsContent
from gui.windows.base_window import PopupWindow


class SettingsWindow(PopupWindow):
    _name = 'Settings'

    _curr_nav_idx = 0
    _contents = [UserSettingsContent, ProjectSettingsContent, ImguiSettingsContent]
    _content_names_list = ['User Settings', 'Project Settings', 'Imgui Settings']

    @classmethod
    def w_init(cls):
        super().w_init()

    @classmethod
    def w_update(cls):
        super().w_update()
    @classmethod
    def w_content(cls):
        c.begin_child('settings selector', width=imgui.get_window_width()/3, height=0, border=True)
        for i in range(len(cls._contents)):
            clicked, state = imgui.menu_item(cls._content_names_list[i], None, cls._curr_nav_idx == i)
            if clicked:
                cls.switch_content(i)
        imgui.end_child()
        imgui.same_line()
        c.begin_child('settings content', )
        cls._contents[cls._curr_nav_idx].c_show()
        imgui.end_child()

    @classmethod
    def w_open(cls):
        super().w_open()
        cls._contents[cls._curr_nav_idx].c_on_show()

    @classmethod
    def w_close(cls):
        super().w_close()
        cls._contents[cls._curr_nav_idx].c_on_hide()

    @classmethod
    def switch_content(cls, idx):
        if idx == cls._curr_nav_idx:
            return
        org_content = cls._contents[cls._curr_nav_idx]
        org_content.c_on_hide()
        new_content = cls._contents[idx]
        new_content.c_on_show()
        cls._curr_nav_idx = idx
