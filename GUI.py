import logging
import os

import imgui
import moderngl_window as mglw
from ImNodeEditor import NE
from moderngl_window.integrations.imgui import ModernglWindowRenderer

from gui import global_info
from gui import global_var as g
from gui.ui_manager import UIManager

# 配置日志记录器
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')  # 设置日志记录器的级别为 DEBUG


# ctypes.windll.user32.SetProcessDPIAware()

class WindowEvents(mglw.WindowConfig):
    gl_version = (3, 3)
    title = global_info.PROJECT_NAME
    aspect_ratio = None
    vsync = True
    window_size = (1280 * g.GLOBAL_SCALE, 720 * g.GLOBAL_SCALE)
    resource_dir = r'gui/resources'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        imgui.create_context()
        NE.set_window_event(self)
        g.mFirstLoop = True
        g.mWindowEvent = self
        g.mWindowSize = self.wnd.size
        self.init_fonts()
        self.imgui = ModernglWindowRenderer(self.wnd)
        # start ui manager
        UIManager.u_init()

        # scroll
        self.target_scroll_y = 0.0

    def init_fonts(self):
        _ = self
        io = imgui.get_io()
        g.mFont = io.fonts.add_font_from_file_ttf(
            os.path.join(g.GUI_RESOURCES_ROOT, 'fonts/arial.ttf'), g.FONT_SIZE,
            glyph_ranges=io.fonts.get_glyph_ranges_chinese_full())
        g.mFontBold = io.fonts.add_font_from_file_ttf(
            os.path.join(g.GUI_RESOURCES_ROOT, 'fonts/arialbd.ttf'), g.FONT_SIZE,
            glyph_ranges=io.fonts.get_glyph_ranges_chinese_full())
        g.mNodeEditorFont = io.fonts.add_font_from_file_ttf(
            os.path.join(g.GUI_RESOURCES_ROOT, 'fonts/arial.ttf'), 16,
            glyph_ranges=io.fonts.get_glyph_ranges_chinese_full())
        g.mNodeEditorFontBold = io.fonts.add_font_from_file_ttf(
            os.path.join(g.GUI_RESOURCES_ROOT, 'fonts/arialbd.ttf'), 16,
            glyph_ranges=io.fonts.get_glyph_ranges_chinese_full())

    def render(self, time: float, frametime: float):
        # main loop
        self.update(time, frametime)  # logical update
        self.render_ui()  # ui update

    def update(self, time, frametime):
        # logical update
        g.mTime = time
        g.mFrametime = frametime if frametime > 0 else 1e-5
        UIManager.u_update()
        self.handle_smooth_scroll(frametime)

    def render_ui(self):
        """Render the UI"""
        self.wnd.use()
        # ui update
        imgui.new_frame()
        with imgui.font(g.mFont):
            UIManager.u_render_ui()
        imgui.render()
        self.imgui.render(imgui.get_draw_data())
        g.mFirstLoop = False

    def handle_smooth_scroll(self, frametime):
        # handle mouse scroll event
        if abs(self.target_scroll_y) < 0.15:
            self.target_scroll_y = 0.0
        percent = min(8.0 * frametime, 1.0)
        delta_y = self.target_scroll_y * percent
        self.target_scroll_y -= delta_y
        self.imgui.mouse_scroll_event(0, delta_y)
        UIManager.u_mouse_scroll_event_smooth(0, delta_y)

    def resize(self, width: int, height: int):
        g.mWindowSize = self.wnd.size
        self.imgui.resize(width, height)
        UIManager.u_resize(width, height)

    def key_event(self, key, action, modifiers):
        self.imgui.key_event(key, action, modifiers)
        UIManager.u_key_event(key, action, modifiers)

    def mouse_position_event(self, x, y, dx, dy):
        self.imgui.mouse_position_event(x, y, dx, dy)
        UIManager.u_mouse_position_event(x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        self.imgui.mouse_drag_event(x, y, dx, dy)
        UIManager.u_mouse_drag_event(x, y, dx, dy)

    def mouse_scroll_event(self, x_offset, y_offset):
        self.target_scroll_y += y_offset  # handle mouse smooth scroll event in update
        UIManager.u_mouse_scroll_event(x_offset, y_offset)

    def mouse_press_event(self, x, y, button):
        self.imgui.mouse_press_event(x, y, button)
        UIManager.u_mouse_press_event(x, y, button)

    def mouse_release_event(self, x: int, y: int, button: int):
        self.imgui.mouse_release_event(x, y, button)
        UIManager.u_mouse_release_event(x, y, button)

    def unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)
        UIManager.u_unicode_char_entered(char)

    def files_dropped_event(self, x, y, paths):
        UIManager.u_files_dropped_event(x, y, paths)


if __name__ == '__main__':
    mglw.run_window_config(WindowEvents)
