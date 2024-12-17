# This Python program is created for academic purposes only.
# Modification and commercial use are allowed with proper attribution to the author.

# This code is the main entry point for the program's UI, developed based on moderngl window

# Author: [YiHeng FENG]
# Affiliation: [Inst. AAA, School of Architecture, Southeast University, Nanjing]

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')  # Set the logging level of the logger to DEBUG
logging.getLogger("PIL").setLevel(logging.WARNING)  # Disable PIL's DEBUG output
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import sys
import os

# Add src folder to sys.path
path = os.path.join(os.getcwd(), "src")
if path not in sys.path:
    sys.path.append(path)

# We use imgui and moderngl_window to render the gui and window, the backend by default is pyglet
import imgui
import moderngl_window as mglw
from moderngl_window.integrations.imgui import ModernglWindowRenderer

# My custom NodeEditor plugin
from ImNodeEditor import NE

# Loading order: global_info => user_data / user_settings => global_app_state
# The latter can reference the former, while the former theoretically should not reference the latter
from gui.global_info import *  # global info stores program constants, which generally should not be modified by users
from gui.user_data import user_data  # User data will change with user operations and will be saved when the user exits
from gui.global_app_state import g  # global_app_state records public variables during program runtime, which will not be saved when the user exits

# The UI Manager controls all UI behaviors
from gui.ui_manager import UIManager
# The Project Manager controls all project related behaviours
from scripts.project_manager import ProjectManager

# Import modules
from gui.modules import FontModule

# Set DPI scaling, the following two lines can be disabled
import ctypes

ctypes.windll.user32.SetProcessDPIAware()


class WindowEvents(mglw.WindowConfig):
    gl_version = (4, 2)
    title = PROJECT_NAME
    aspect_ratio = None
    vsync = True
    window_size = user_data.window_size
    resource_dir = RESOURCES_DIR

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Uncomment the next line in the release version to disable the ESC exit functionality.
        # self.wnd.exit_key = None

        imgui.create_context()
        NE.set_window_event(self)

        # Init global app state
        g.mFirstLoop = True
        g.mWindowEvent = self
        g.mWindowSize = self.wnd.size

        FontModule.m_create_fonts()

        self.imgui = ModernglWindowRenderer(self.wnd)  # create imgui renderer after all modules are inited

        # Init Managers
        UIManager.u_init()  # init UI manager
        ProjectManager.p_init()  # init Project Manager

        # Scroll
        self.target_scroll_y = 0.0

        # We put the full-screen handling in the __init__ instead of using class static variables to
        # prevent issues with window scaling when specifying full-screen at the beginning and exiting full-screen.
        # This may be due to a lack of comprehensive understanding of how to use the moderngl window.
        # However, the approach used here does indeed solve the problem.
        if user_data.fullscreen:
            self.wnd.fullscreen = True

    def render(self, time: float, frametime: float):
        """
        Main loop
        This is the main loop function specified by the moderngl window.
        We have divided it into three parts: update, render_ui, and late_update.
        update and late_update mainly handle logic, while render_ui is responsible for generating and rendering UI components.
        """
        self._update(time, frametime)  # logical update

        self._render_ui()  # ui rendering

        self._late_update()  # the late logical update

    def _update(self, time: float, frametime: float):
        """
        Logical update
        """

        g.mTime = time
        g.mFrametime = max(frametime, 1e-5)  # mFrametime should not be zero

        # handle ui logical update
        UIManager.u_update()
        # update ProjectManager
        ProjectManager.p_update()

        # handle smooth scroll
        self.handle_smooth_scroll(frametime)

    def _render_ui(self):
        """
        Render the UI
        """

        imgui.new_frame()
        UIManager.u_render_ui()  # ui elements are generated here, but not yet rendered

        # render to ctx.screen
        self.wnd.use(), imgui.render(), self.imgui.render(imgui.get_draw_data())

    def _late_update(self):
        _ = self
        UIManager.u_late_update()
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
        logger.debug(f"mouse pressed, x = {x}, y = {y}, button = {button}")

    def mouse_release_event(self, x: int, y: int, button: int):
        self.imgui.mouse_release_event(x, y, button)
        UIManager.u_mouse_release_event(x, y, button)
        logger.debug(f"mouse released, x = {x}, y = {y}, button = {button}")

    def unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)
        UIManager.u_unicode_char_entered(char)

    def files_dropped_event(self, x, y, paths):
        UIManager.u_files_dropped_event(x, y, paths)

    def close(self):
        """ is ready to close"""
        if g.mIsClosing:
            # double click close button will close the window immediately
            g.mConfirmClose = True
            return
        g.mIsClosing = True
        UIManager.u_ready_to_close()

    @classmethod
    def run(cls, args=None, timer=None):
        """
        overrides WindowEvents.run()
        """
        from moderngl_window import setup_basic_logging, create_parser, parse_args, get_local_window_cls, activate_context
        from moderngl_window.timers.clock import Timer
        import weakref

        setup_basic_logging(cls.log_level)
        parser = create_parser()
        cls.add_arguments(parser)
        values = parse_args(args=args, parser=parser)
        cls.argv = values
        window_cls = get_local_window_cls(values.window)

        # Calculate window size
        size = values.size or cls.window_size
        size = int(size[0] * values.size_mult), int(size[1] * values.size_mult)

        # Resolve cursor
        show_cursor = values.cursor
        if show_cursor is None:
            show_cursor = cls.cursor
        window = window_cls(
            title=cls.title,
            size=size,
            fullscreen=cls.fullscreen or values.fullscreen,
            resizable=values.resizable
            if values.resizable is not None
            else cls.resizable,
            gl_version=cls.gl_version,
            aspect_ratio=cls.aspect_ratio,
            vsync=values.vsync if values.vsync is not None else cls.vsync,
            samples=values.samples if values.samples is not None else cls.samples,
            cursor=show_cursor if show_cursor is not None else True,
            backend=values.backend,
        )
        window.print_context_info()
        activate_context(window=window)
        timer = timer or Timer()
        config = cls(ctx=window.ctx, wnd=window, timer=timer)
        # Avoid the event assigning in the property setter for now
        # We want the even assigning to happen in WindowConfig.__init__
        # so users are free to assign them in their own __init__.
        window._config = weakref.ref(config)

        # Swap buffers once before staring the main loop.
        # This can trigged additional resize events reporting
        # a more accurate buffer size
        window.swap_buffers()
        window.set_default_viewport()

        timer.start()

        while not g.mConfirmClose:
            current_time, delta = timer.next_frame()

            if config.clear_color is not None:
                window.clear(*config.clear_color)

            # Always bind the window framebuffer before calling render
            window.use()

            window.render(current_time, delta)

            if not g.mConfirmClose:
                window.swap_buffers()

        _, duration = timer.stop()
        window.destroy()
        if duration > 0:
            logger.info(
                "Duration: {0:.2f}s @ {1:.2f} FPS".format(
                    duration, window.frames / duration
                )
            )


if __name__ == '__main__':
    WindowEvents.run()
