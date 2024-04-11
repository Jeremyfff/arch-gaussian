import imgui
from ImNodeEditor import NE
from gui.modules import LayoutModule, EventModule, ShadowModule, ALL_MODULES
from gui.windows import ALL_WINDOWS, POPUP_WINDOWS
from scripts.project_manager import ProjectManager
from gui import global_var as g

class UIManager:

    @classmethod
    def u_init(cls):
        for module in ALL_MODULES:
            module.m_init()
        for window in ALL_WINDOWS:
            window.w_init()

    @classmethod
    def u_update(cls):
        """logical update"""
        if ProjectManager.curr_project is not None:
            ProjectManager.curr_project.p_update()

        for window in ALL_WINDOWS:
            window.w_update()

    @classmethod
    def u_render_ui(cls):
        """ui update"""
        for window in ALL_WINDOWS:
            window.w_show()
        ShadowModule.update_window_rects(POPUP_WINDOWS)
        imgui.show_demo_window()

    @classmethod
    def u_resize(cls, width: int, height: int):
        LayoutModule.on_resize()
        EventModule.resize(width, height)

    @classmethod
    def u_key_event(cls, key, action, modifiers):
        NE.handle_key_event(key, action, modifiers)
        EventModule.key_event(key, action, modifiers)
        if action=="ACTION_PRESS":
            if key == 65505:
                g.mShiftDown = True
            if key == 65507:
                g.mCtrlDown = True
        elif action == "ACTION_RELEASE":
            if key == 65505:
                g.mShiftDown = False
            if key == 65507:
                g.mCtrlDown = False
    @classmethod
    def u_mouse_position_event(cls, x, y, dx, dy):
        NE.handle_mouse_position_event(x, y, dx, dy)
        EventModule.mouse_position_event(x, y, dx, dy)

    @classmethod
    def u_mouse_drag_event(cls, x, y, dx, dy):
        NE.handle_mouse_drag_event(x, y, dx, dy)
        EventModule.mouse_drag_event(x, y, dx, dy)

    @classmethod
    def u_mouse_scroll_event_smooth(cls, x_offset, y_offset):
        EventModule.mouse_scroll_event_smooth(x_offset, y_offset)

    @classmethod
    def u_mouse_scroll_event(cls, x_offset, y_offset):
        NE.handle_mouse_scroll_event(x_offset, y_offset)
        EventModule.mouse_scroll_event(x_offset, y_offset)

    @classmethod
    def u_mouse_press_event(cls, x, y, button):
        NE.handle_mouse_press_event(x, y, button)
        EventModule.mouse_press_event(x, y, button)

    @classmethod
    def u_mouse_release_event(cls, x: int, y: int, button: int):
        NE.handle_mouse_release_event(x, y, button)
        EventModule.mouse_release_event(x, y, button)

    @classmethod
    def u_unicode_char_entered(cls, char):
        EventModule.unicode_char_entered(char)

    @classmethod
    def u_files_dropped_event(cls, x, y, paths):
        EventModule.files_dropped_event(x, y, paths)
