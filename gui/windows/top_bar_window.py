import os

import imgui

from gui import components as c
from gui import global_var as g
from gui.modules import texture_module, LayoutModule
from gui.utils import io_utils
from gui.windows.base_window import BaseWindow
from scripts import project_manager as pm


class TopBarWindow(BaseWindow):
    LAYOUT_NAME = 'level1_top'

    # 项目名列表
    project_names = [
        "SkyNet AI Assistant",
        "Quantum Fusion Reactor",
        "Hyperloop Transport System",
        "Virtual Reality Oasis",
        "NanoBot Medical Scanner",
        "SpaceX Mars Colonization Project",
        "SmartCity IoT Platform",
        "CleanEnergy Solar Farm Initiative",
        "AugmentedReality Enhanced Education",
        "HealthTech Wearable Devices"
    ]

    # 项目地址列表（本地文件夹路径）
    project_paths = [
        "/path/to/SkyNet_AI_Assistant",
        "/path/to/Quantum_Fusion_Reactor",
        "/path/to/Hyperloop_Transport_System",
        "/path/to/Virtual_Reality_Oasis",
        "/path/to/NanoBot_Medical_Scanner",
        "/path/to/SpaceX_Mars_Colonization_Project",
        "/path/to/SmartCity_IoT_Platform",
        "/path/to/CleanEnergy_Solar_Farm_Initiative",
        "/path/to/AugmentedReality_Enhanced_Education",
        "/path/to/HealthTech_Wearable_Devices"
    ]
    _confirm_create_project = False
    _confirm_create_project_path = ''

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
            imgui.set_cursor_pos_x(
                imgui.get_cursor_pos_x() + imgui.get_content_region_available_width() - g.mImguiStyle.window_padding[
                    0] - imgui.get_frame_height())
            c.icon_button('settings-4-fill')

            if imgui.begin_popup('main_menu_popup_on_top_bar_window'):
                from gui.contents import MainMenuContent
                MainMenuContent.c_show()
                imgui.end_popup()

            # end ===================================================================================
        imgui.pop_style_var(2)

    @classmethod
    def show_project_button(cls):
        button_content = 'Create or Open Project' if pm.curr_project is None else pm.curr_project.project_name
        button_icon = 'play-list-add-line' if pm.curr_project is None else texture_module.generate_character_icon(
            pm.curr_project.project_name.upper()[0])
        button_tooltip = 'Click To Open' if pm.curr_project is None else pm.curr_project.project_root
        cursor_pos = imgui.get_cursor_pos()
        popup_cursor_pos = (cursor_pos[0], cursor_pos[1] + LayoutModule.layout.get_size(cls.LAYOUT_NAME)[1])
        # project button
        if c.icon_text_button(button_icon, button_content):
            imgui.open_popup('project_button_popup')
        c.easy_tooltip(button_tooltip)
        if imgui.is_popup_open('project_button_popup'):
            imgui.set_next_window_position(*popup_cursor_pos)
            imgui.set_next_window_size(300 * g.GLOBAL_SCALE, 500 * g.GLOBAL_SCALE)
        # project button popup
        if imgui.begin_popup('project_button_popup'):
            imgui.push_style_color(imgui.COLOR_BUTTON, 0, 0, 0, 0)
            imgui.push_style_var(imgui.STYLE_BUTTON_TEXT_ALIGN, (0.0, 0.5))
            if pm.curr_project is not None:
                imgui.text(pm.curr_project.project_root)
                # save project button
                if c.icon_text_button('save-line', 'Save Project', width=imgui.get_content_region_available_width()):
                    pm.curr_project.save()
                    imgui.close_current_popup()
            # open project button
            if c.icon_text_button('folder-open-line', 'Open Project', width=imgui.get_content_region_available_width()):
                folder_path = io_utils.open_folder_dialog()
                if folder_path:
                    project = pm.Project.open_folder_as_project(folder_path)
                    if project is None:
                        # project not created yet
                        cls._confirm_create_project_path = folder_path
                        cls._confirm_create_project = True
                    else:
                        pm.curr_project = project
                imgui.close_current_popup()
            # create project button
            if c.icon_text_button('folder-add-line', 'Create Project',
                                  width=imgui.get_content_region_available_width()):
                folder_path = io_utils.open_folder_dialog()
                if folder_path:
                    project = pm.Project.create_project(os.path.basename(folder_path), folder_path)
                    pm.curr_project = project
                imgui.close_current_popup()
            imgui.separator()
            # recent projects
            imgui.text('Recent Projects:')
            for i in range(len(cls.project_names)):
                project_name = cls.project_names[i]
                project_path = cls.project_paths[i]
                character = project_name[0].upper()
                texture_module.generate_character_icon(character)
                if c.icon_double_text_button(character, project_name, project_path,
                                             width=imgui.get_content_region_available_width()):
                    imgui.close_current_popup()
            imgui.pop_style_color()
            imgui.pop_style_var()
            imgui.end_popup()
        # create project confirm popup
        c.create_project_confirm_popup(cls._confirm_create_project, cls._confirm_create_project_path)
