import os

import imgui

from gui.components import c
from gui.global_app_state import g
from gui.modules import TextureModule, LayoutModule
from gui.user_data import user_data
from gui.utils import io_utils
from gui.windows.base_window import BaseWindow
from scripts.project_manager import ProjectManager


class TopBarWindow(BaseWindow):
    TRANSLATION_FILE_NAME = os.path.basename(__file__).replace(".py", ".csv")
    LAYOUT_NAME = 'level1_top'

    recent_project_names = []
    recent_project_paths = []

    # misc
    _cached_default_button_active_color = None
    _cached_button_active_color_for_recent_projects_buttons = None

    @classmethod
    def w_init(cls):
        super().w_init()
        cls._cached_default_button_active_color = g.mImguiStyle.colors[imgui.COLOR_BUTTON_ACTIVE]
        tmp = cls._cached_default_button_active_color
        cls._cached_button_active_color_for_recent_projects_buttons = (tmp[0], tmp[1], tmp[2], tmp[3] * 0.5)

    @classmethod
    def w_update(cls):
        super().w_update()

    @classmethod
    def w_show(cls, **kwargs):
        super().w_show()
        org_window_padding = g.mImguiStyle.window_padding
        org_frame_padding = g.mImguiStyle.frame_padding
        new_window_padding = (8 * g.global_scale, 4 * g.global_scale)
        new_frame_padding = (8 * g.global_scale, org_frame_padding[1] + org_window_padding[1] - new_window_padding[1])
        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, new_window_padding)
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, new_frame_padding)

        flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
        flags |= imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE

        with LayoutModule.LayoutWindow(cls.LAYOUT_NAME, flags=flags):
            # begin ===================================================================================
            if c.icon_button('bar-chart-horizontal-line', tint_color=(0.8, 0.8, 0.8, 1), tooltip=cls._l.get_translation('Menu')):
                imgui.open_popup('main_menu_popup_on_top_bar_window')

            imgui.same_line()
            imgui.set_cursor_pos_x(imgui.get_cursor_pos_x() + 20 * g.global_scale)
            imgui.set_cursor_pos_y(g.mImguiStyle.window_padding[1] + g.mImguiStyle.frame_padding[1])
            imgui.text('ARCH-GAUSSIAN')
            imgui.same_line()
            imgui.set_cursor_pos_y(g.mImguiStyle.window_padding[1])
            cls.show_project_button()

            c.move_to_horizontal_right(3)

            if g.mWindowEvent.wnd.fullscreen:
                if c.icon_button('fullscreen-exit', id="fullscreen_button_exit", tooltip=cls._l.get_translation("Exit FullScreen")):
                    g.mWindowEvent.wnd.fullscreen = False
                    user_data.fullscreen = False
            else:
                if c.icon_button('fullscreen', id="fullscreen_button", tooltip=cls._l.get_translation("Enter FullScreen")):
                    g.mWindowEvent.wnd.fullscreen = True
                    user_data.fullscreen = True
            imgui.same_line()
            if c.icon_button('setting', id="settings_button", tooltip=cls._l.get_translation("Settings")):
                from gui.windows import SettingsWindow
                SettingsWindow.w_open()
            imgui.same_line()
            if c.icon_button('logout', id="logout_button", tooltip=cls._l.get_translation("Exit")):
                g.mWindowEvent.close()

            if imgui.begin_popup('main_menu_popup_on_top_bar_window'):
                from gui.contents import MainMenuContent
                MainMenuContent.c_show()
                imgui.end_popup()
            # end ===================================================================================
        imgui.pop_style_var(2)

    @classmethod
    def show_project_button(cls):
        _confirm_create_project = False
        _confirm_create_project_path = ''

        button_content = cls._l.get_translation('Create or Open Project') if ProjectManager.curr_project is None \
            else ProjectManager.get_curr_project_name()
        button_icon = 'play-list-add-line' if ProjectManager.curr_project is None \
            else TextureModule.generate_character_icon(ProjectManager.get_curr_project_name().upper()[0])
        button_tooltip = cls._l.get_translation('Click To Open') if ProjectManager.curr_project is None \
            else ProjectManager.get_curr_project_root()
        cursor_pos = imgui.get_cursor_pos()
        popup_cursor_pos = (cursor_pos[0], cursor_pos[1] + LayoutModule.layout.get_size(cls.LAYOUT_NAME)[1])
        # project button
        if c.icon_text_button(button_icon, button_content):
            imgui.open_popup('project_button_popup')
            cls.recent_project_names = user_data.recent_project_names[::-1]
            cls.recent_project_paths = user_data.recent_project_paths[::-1]
        c.easy_tooltip(button_tooltip)
        if imgui.is_popup_open('project_button_popup'):
            imgui.set_next_window_position(*popup_cursor_pos)
            imgui.set_next_window_size(300 * g.global_scale, min(500 * g.global_scale, g.mWindowSize[1] - LayoutModule.layout.get_size("level1_top")[1]))
        # project button popup
        if imgui.begin_popup('project_button_popup', imgui.WINDOW_NONE):
            imgui.push_style_color(imgui.COLOR_BUTTON, 0, 0, 0, 0)
            imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *cls._cached_button_active_color_for_recent_projects_buttons)
            imgui.push_style_var(imgui.STYLE_BUTTON_TEXT_ALIGN, (0.0, 0.5))
            if ProjectManager.curr_project is not None:
                imgui.text(ProjectManager.curr_project.project_root)
                # save project button
                if c.icon_text_button('save-line', cls._l.get_translation('Save Project'), width=imgui.get_content_region_available_width()):
                    ProjectManager.save_curr_project()
                    imgui.close_current_popup()
            # open project button
            if c.icon_text_button('folder-open-line', cls._l.get_translation('Open Project'), width=imgui.get_content_region_available_width()):
                folder_path = io_utils.open_folder_dialog()
                if folder_path:
                    ProjectManager.save_curr_project()
                    project = ProjectManager.open_folder_as_project(folder_path)
                    if project is None:  # project not created yet
                        _confirm_create_project_path = folder_path
                        _confirm_create_project = True
                imgui.close_current_popup()
            # create project button
            if c.icon_text_button('folder-add-line', cls._l.get_translation('Create Project'),
                                  width=imgui.get_content_region_available_width()):
                folder_path = io_utils.open_folder_dialog()
                if folder_path:
                    ProjectManager.create_project(os.path.basename(folder_path), folder_path)
                imgui.close_current_popup()
            imgui.separator()
            # recent projects
            imgui.text(cls._l.get_translation('Recent Projects:'))
            for i in range(len(cls.recent_project_names)):
                project_name = cls.recent_project_names[i]
                project_path = cls.recent_project_paths[i]
                character = project_name[0].upper()
                TextureModule.generate_character_icon(character)
                if c.icon_double_text_button(character, project_name, project_path,
                                             width=imgui.get_content_region_available_width()):
                    ProjectManager.save_curr_project()
                    ProjectManager.open_folder_as_project(cls.recent_project_paths[i])
                    imgui.close_current_popup()
            imgui.pop_style_color(2)
            imgui.pop_style_var()
            imgui.end_popup()
        # create project confirm popup
        c.create_project_confirm_popup(_confirm_create_project, _confirm_create_project_path)
