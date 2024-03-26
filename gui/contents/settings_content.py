import imgui

from gui import components as c
from gui import global_userinfo
from gui.contents.base_content import BaseContent


class UserSettingsContent(BaseContent):
    _cached_user_settings_types = None

    @classmethod
    def c_init(cls):
        super().c_init()
        cls._cached_user_settings_types = c.get_arg_types(global_userinfo.user_settings)

    @classmethod
    def c_update(cls):
        super().c_update()

    @classmethod
    def c_show(cls):
        super().c_show()
        imgui.text('user settings')
        c.arg_editor(global_userinfo.user_settings, cls._cached_user_settings_types)

    @classmethod
    def c_on_show(cls):
        super().c_on_show()

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()


class ProjectSettingsContent(BaseContent):
    @classmethod
    def c_init(cls):
        super().c_init()

    @classmethod
    def c_update(cls):
        super().c_update()

    @classmethod
    def c_show(cls):
        super().c_show()
        imgui.text('project settings content')

    @classmethod
    def c_on_show(cls):
        super().c_on_show()

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()
