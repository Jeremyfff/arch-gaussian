import os
import threading

import imgui

from gui.components import c
from gui.contents.base_content import BaseContent
from gui.global_app_state import g
from gui.global_info import *
from gui.modules import StyleModule, EventModule
from gui.modules.cell_module import CellModule
from gui.user_data import user_data, user_settings


class UserSettingsContent(BaseContent):
    """
    在此处创建自定义的用户设置UI界面
    """
    TRANSLATION_FILE_NAME = os.path.basename(__file__).replace(".py", ".csv")

    _cell_module: CellModule = None

    _languages_str_list = []
    _target_language_to_set_in_next_frame = -1

    # cache
    _cached_local_colmap_executable_path: str = None  # 用于记录本机的colmap应该什么位置

    @classmethod
    def c_init(cls):
        super().c_init()
        threading.Thread(target=cls._init_thread).start()
        cls._cell_module = CellModule(language_set=cls._l)
        cls._cell_module.register_and_add_cell_to_display_queue("Language Settings", cls._language_settings_cell)
        cls._cell_module.register_and_add_cell_to_display_queue("Folder Settings", cls._folder_settings_cell)
        cls._cell_module.register_and_add_cell_to_display_queue("Scroll Settings", cls._scroll_settings_cell)
        cls._cell_module.register_and_add_cell_to_display_queue("3D View Settings", cls._3d_view_settings_cell)
        cls._cell_module.register_and_add_cell_to_display_queue("Advanced Settings", cls._advanced_settings_cell)

        cls._languages_str_list = [cls._l.get_translation(language) for language in LANGUAGES]
        EventModule.register_language_change_callback(cls._on_language_change)

    @classmethod
    def _init_thread(cls):
        from gui.utils.io_utils import find_colmap_executable
        cls._cached_local_colmap_executable_path = find_colmap_executable()

    @classmethod
    def c_update(cls):
        super().c_update()
        if cls._target_language_to_set_in_next_frame >= 0:
            user_settings.language = cls._target_language_to_set_in_next_frame
            EventModule.on_language_change()
            cls._target_language_to_set_in_next_frame = -1

    @classmethod
    def c_show(cls):
        super().c_show()
        cls._cell_module.show()

    @classmethod
    def c_on_show(cls):
        super().c_on_show()
        g.mIsUserSettingsContentOpen = True

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()
        g.mIsUserSettingsContentOpen = False

    # region Cells

    @classmethod
    def _language_settings_cell(cls):
        changed, new_language = imgui.combo(cls._l.get_translation("Select Language"), user_settings.language, cls._languages_str_list)
        if changed and new_language != user_settings.language:
            cls._target_language_to_set_in_next_frame = new_language

    @classmethod
    def _folder_settings_cell(cls):
        """Folder Settings"""
        _half_width = imgui.get_content_region_available_width() * 0.5

        # repository folder
        _, user_settings.project_repository_folder = c.file_or_folder_selector(cls._l.get_translation("Project Repository Folder"), user_settings.project_repository_folder, _half_width, False)

        # colmap executable path, 添加自动搜索
        _, user_settings.colmap_executable = c.file_or_folder_selector(cls._l.get_translation("Colmap Executable"), user_settings.colmap_executable, _half_width, True)
        if cls._cached_local_colmap_executable_path is not None and user_settings.colmap_executable != cls._cached_local_colmap_executable_path:
            imgui.push_style_color(imgui.COLOR_TEXT, *StyleModule.COLOR_RED)
            imgui.text(cls._l.get_translation("Invalid Colmap Executable Path"))
            imgui.pop_style_color(1)
            imgui.same_line()
            if imgui.button(cls._l.get_translation("Auto Search Colmap Executable")):
                from gui.utils.io_utils import find_colmap_executable
                user_settings.colmap_executable = find_colmap_executable()
                cls._cached_local_colmap_executable_path = user_settings.colmap_executable

    @classmethod
    def _scroll_settings_cell(cls):
        """Scroll Speed Settings"""
        _, user_settings.move_scroll_speed = imgui.input_float(cls._l.get_translation("Move Scroll Speed"), user_settings.move_scroll_speed)
        _, user_settings.scale_scroll_speed = imgui.input_float(cls._l.get_translation("Scale Scroll Speed"), user_settings.scale_scroll_speed)
        _, user_settings.rotate_scroll_speed = imgui.input_float(cls._l.get_translation("Rotate Scroll Speed"), user_settings.rotate_scroll_speed)

    @classmethod
    def _3d_view_settings_cell(cls):
        """三维视图设置"""
        c.warning_text(cls._l.get_translation("Need Restart"))
        _, user_settings.grid_fading_distance = imgui.slider_float(cls._l.get_translation("Grid Fading Dist"), user_settings.grid_fading_distance, 0.01, 100.0, '%.1f')
        c.easy_tooltip(cls._l.get_translation("Sets the gradient disappearance distance of the 3D view grid. Beyond this distance, the coordinate grid will not be visible."))
        _, user_settings.grid_z_offset = imgui.input_float(cls._l.get_translation("Grid Z Offset"), user_settings.grid_z_offset)
        c.easy_tooltip(cls._l.get_translation("Sets the z-offset distance of the grid. The purpose of this option is to allow this option to be kept very small."))

    @classmethod
    def _advanced_settings_cell(cls):
        # 高级设置

        if imgui.button(cls._l.get_translation("Revert to default(Need restart)")):
            user_settings.__init__()
        c.easy_tooltip(cls._l.get_translation("This option will reset all user settings"))
        if imgui.button(cls._l.get_translation("Clear all user data(Need restart)")):
            user_data.__init__()
        c.easy_tooltip(cls._l.get_translation("This option will delete all user data"))

    # endregion

    @classmethod
    def _on_language_change(cls):
        cls._languages_str_list = [cls._l.get_translation(language) for language in LANGUAGES]


class ProjectSettingsContent(BaseContent):
    TRANSLATION_FILE_NAME = os.path.basename(__file__).replace(".py", ".csv")

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


class ImguiSettingsContent(BaseContent):
    TRANSLATION_FILE_NAME = os.path.basename(__file__).replace(".py", ".csv")

    @classmethod
    def c_init(cls):
        super().c_init()

    @classmethod
    def c_update(cls):
        super().c_update()

    @classmethod
    def c_show(cls):
        super().c_show()
        imgui.show_style_editor(imgui.get_style())

    @classmethod
    def c_on_show(cls):
        super().c_on_show()

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()


class StyleSettingsContent(BaseContent):
    TRANSLATION_FILE_NAME = os.path.basename(__file__).replace(".py", ".csv")

    _new_global_scale_value = -1
    _global_scale_values = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
    _global_scale_values_str = ['0.5', '0.75', '1.0', '1.25', '1.5', '1.75', '2.0']
    _curr_global_scale_combo_idx = -1

    _fs_blur_radius_values = [4, 8, 16, 32, 64, 128, 256]
    _fs_blur_radius_values_str = ['4', '8', '16', '32', '64', '128', '256']
    _curr_fs_blur_radius_combo_idx = -1

    _is_mouse_hovering_bg_style_region = False
    _mouse_scroll_x_in_this_frame, _mouse_scroll_y_in_this_frame = 0, 0
    _bg_style_region_scroll_pos_x = 0.0

    # misc
    _global_scale_updated_in_this_frame = False

    @classmethod
    def c_init(cls):
        super().c_init()
        cls._new_global_scale_value = g.global_scale
        try:
            cls._curr_global_scale_combo_idx = cls._global_scale_values.index(g.global_scale)
        except:
            cls._curr_global_scale_combo_idx = -1

        try:
            cls._curr_fs_blur_radius_combo_idx = cls._fs_blur_radius_values.index(user_settings.full_screen_blur_radius)
        except:
            cls._curr_fs_blur_radius_combo_idx = -1

    @classmethod
    def c_update(cls):
        super().c_update()
        if cls._global_scale_updated_in_this_frame:
            EventModule.on_global_scale_change()
            cls._global_scale_updated_in_this_frame = False

    @classmethod
    def c_show(cls):
        super().c_show()
        # global scale
        changed, cls._curr_global_scale_combo_idx = imgui.combo(cls._l.get_translation("Global Scale"), cls._curr_global_scale_combo_idx, cls._global_scale_values_str)
        if changed:
            user_settings.global_scale = cls._global_scale_values[cls._curr_global_scale_combo_idx]
            cls._global_scale_updated_in_this_frame = True

        imgui.separator()

        # blur settings
        c.gray_text(cls._l.get_translation("Full Screen Blur Settings"))
        changed, user_settings.full_screen_blur_fbt_down_sampling_factor = imgui.slider_int(cls._l.get_translation("Down Sample"), user_settings.full_screen_blur_fbt_down_sampling_factor, 1, 16)
        changed, cls._curr_fs_blur_radius_combo_idx = imgui.combo(cls._l.get_translation("Blur Radius"), cls._curr_fs_blur_radius_combo_idx, cls._fs_blur_radius_values_str)
        if changed:
            user_settings.full_screen_blur_radius = cls._fs_blur_radius_values[cls._curr_fs_blur_radius_combo_idx]

        c.gray_text(cls._l.get_translation("The best combination is: down sample * 16 = blur radius."))
        c.gray_text(f"{user_settings.full_screen_blur_fbt_down_sampling_factor} x 16 = {user_settings.full_screen_blur_fbt_down_sampling_factor * 16}")

        imgui.separator()

        # theme settings
        c.gray_text(cls._l.get_translation("Background Theme Settings"))
        c.begin_child_auto_height("bg_style_region", initial_height=0, flags=imgui.WINDOW_HORIZONTAL_SCROLLING_BAR)
        if imgui.is_window_hovered(imgui.HOVERED_CHILD_WINDOWS):
            cls._bg_style_region_scroll_pos_x -= (cls._mouse_scroll_x_in_this_frame + cls._mouse_scroll_y_in_this_frame) * 32 * g.global_scale
            cls._bg_style_region_scroll_pos_x = max(min(cls._bg_style_region_scroll_pos_x, imgui.get_scroll_max_x()), 0.0)
        imgui.set_scroll_x(cls._bg_style_region_scroll_pos_x)
        for i in range(NUM_BG_STYLES):
            if i > 0:
                imgui.same_line()
            clicked = c.image_button(f"BgStyle_{i}", width=200 * g.global_scale, height=150 * g.global_scale, bg_color=StyleModule.COLOR_PRIMARY if i == user_settings.bg_style else (0, 0, 0, 0))

            if clicked:
                if user_settings.bg_style != i:
                    user_settings.bg_style = i
                    EventModule.on_bg_style_change()
        c.end_child_auto_height("bg_style_region")

    @classmethod
    def c_on_show(cls):
        super().c_on_show()
        EventModule.register_mouse_scroll_smooth_callback(cls._on_mouse_scroll_smooth)

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()
        EventModule.unregister_mouse_scroll_smooth_callback(cls._on_mouse_scroll_smooth)

    @classmethod
    def _on_mouse_scroll_smooth(cls, x, y):
        cls._mouse_scroll_x_in_this_frame = x
        cls._mouse_scroll_y_in_this_frame = y


class AboutContent(BaseContent):
    TRANSLATION_FILE_NAME = os.path.basename(__file__).replace(".py", ".csv")
    _show_demo_window = False

    @classmethod
    def c_init(cls):
        super().c_init()

    @classmethod
    def c_update(cls):
        super().c_update()

    @classmethod
    def c_show(cls):
        super().c_show()
        imgui.text("write your about info here")
        if imgui.button("show imgui demo window"):
            cls._show_demo_window = True
        if cls._show_demo_window:
            cls._show_demo_window = imgui.show_demo_window(True)

    @classmethod
    def c_on_show(cls):
        super().c_on_show()
        cls._show_demo_window = False

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()
        cls._show_demo_window = False
