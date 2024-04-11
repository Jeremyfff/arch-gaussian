import os

import imgui

from gui import components as c
from gui import global_var as g

from gui.modules import texture_module, LayoutModule, ShadowModule
from gui.utils import io_utils
from gui.windows.base_window import BaseWindow
from scripts.project_manager import ProjectManager


class TopBarWindow(BaseWindow):
    LAYOUT_NAME = 'level1_top'

    recent_project_names = []
    recent_project_paths = []
    @classmethod
    def w_init(cls):
        super().w_init()

    @classmethod
    def w_update(cls):
        super().w_update()

    @classmethod
    def w_show(cls):
        super().w_show()
        org_window_padding = g.mImguiStyle.window_padding
        org_frame_padding = g.mImguiStyle.frame_padding
        new_window_padding = (8, 4)
        new_frame_padding = (8, org_frame_padding[1] + org_window_padding[1] - new_window_padding[1])
        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, new_window_padding)
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, new_frame_padding)

        flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
        flags |= imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE

        with LayoutModule.LayoutWindow(cls.LAYOUT_NAME, flags=flags):
            # begin ===================================================================================
            if c.icon_button('bar-chart-horizontal-line', tint_color=(0.8, 0.8, 0.8, 1), tooltip='menu'):
                imgui.open_popup('main_menu_popup_on_top_bar_window')

            imgui.same_line()
            imgui.set_cursor_pos_x(imgui.get_cursor_pos_x() + 20)
            imgui.set_cursor_pos_y(g.mImguiStyle.window_padding[1] + g.mImguiStyle.frame_padding[1])
            imgui.text('ARCH-GAUSSIAN')
            imgui.same_line()
            imgui.set_cursor_pos_y(g.mImguiStyle.window_padding[1])
            cls.show_project_button()
            imgui.same_line()
            if imgui.button('texture viewer'):
                from gui.windows import TextureViewerWindow
                TextureViewerWindow.w_open()
            imgui.same_line()
            imgui.set_cursor_pos_x(
                imgui.get_cursor_pos_x() + imgui.get_content_region_available_width() - g.mImguiStyle.window_padding[
                    0] - imgui.get_frame_height())
            if c.icon_button('settings-4-fill'):
                from gui.windows import SettingsWindow
                SettingsWindow.w_open()
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

        button_content = 'Create or Open Project' if ProjectManager.curr_project is None \
            else ProjectManager.get_curr_project_name()
        button_icon = 'play-list-add-line' if ProjectManager.curr_project is None \
            else texture_module.generate_character_icon(ProjectManager.get_curr_project_name().upper()[0])
        button_tooltip = 'Click To Open' if ProjectManager.curr_project is None \
            else ProjectManager.get_curr_project_root()
        cursor_pos = imgui.get_cursor_pos()
        popup_cursor_pos = (cursor_pos[0], cursor_pos[1] + LayoutModule.layout.get_size(cls.LAYOUT_NAME)[1])
        # project button
        if c.icon_text_button(button_icon, button_content):
            imgui.open_popup('project_button_popup')
            from gui import global_userinfo
            cls.recent_project_names = global_userinfo.get_user_data("recent_project_names")[::-1]
            cls.recent_project_paths = global_userinfo.get_user_data("recent_project_paths")[::-1]
        c.easy_tooltip(button_tooltip)
        if imgui.is_popup_open('project_button_popup'):
            imgui.set_next_window_position(*popup_cursor_pos)
            imgui.set_next_window_size(300 * g.GLOBAL_SCALE, 500 * g.GLOBAL_SCALE)
        # project button popup
        if imgui.begin_popup('project_button_popup'):
            imgui.push_style_color(imgui.COLOR_BUTTON, 0, 0, 0, 0)
            imgui.push_style_var(imgui.STYLE_BUTTON_TEXT_ALIGN, (0.0, 0.5))
            if ProjectManager.curr_project is not None:
                imgui.text(ProjectManager.curr_project.project_root)
                # save project button
                if c.icon_text_button('save-line', 'Save Project', width=imgui.get_content_region_available_width()):
                    ProjectManager.save_curr_project()
                    imgui.close_current_popup()
            # open project button
            if c.icon_text_button('folder-open-line', 'Open Project', width=imgui.get_content_region_available_width()):
                folder_path = io_utils.open_folder_dialog()
                if folder_path:
                    ProjectManager.save_curr_project()
                    project = ProjectManager.open_folder_as_project(folder_path)
                    if project is None:  # project not created yet
                        _confirm_create_project_path = folder_path
                        _confirm_create_project = True
                imgui.close_current_popup()
            # create project button
            if c.icon_text_button('folder-add-line', 'Create Project',
                                  width=imgui.get_content_region_available_width()):
                folder_path = io_utils.open_folder_dialog()
                if folder_path:
                    ProjectManager.create_project(os.path.basename(folder_path), folder_path)
                imgui.close_current_popup()
            imgui.separator()
            # recent projects
            imgui.text('Recent Projects:')
            for i in range(len(cls.recent_project_names)):
                project_name = cls.recent_project_names[i]
                project_path = cls.recent_project_paths[i]
                character = project_name[0].upper()
                texture_module.generate_character_icon(character)
                if c.icon_double_text_button(character, project_name, project_path,
                                             width=imgui.get_content_region_available_width()):
                    ProjectManager.save_curr_project()
                    ProjectManager.open_folder_as_project(cls.recent_project_paths[i])
                    imgui.close_current_popup()
            imgui.pop_style_color()
            imgui.pop_style_var()
            imgui.end_popup()
        # create project confirm popup
        c.create_project_confirm_popup(_confirm_create_project, _confirm_create_project_path)
