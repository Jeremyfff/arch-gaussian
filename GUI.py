import imgui
import moderngl_window as mglw
from moderngl_window.integrations.imgui import ModernglWindowRenderer
from moderngl_window.context.pyglet.window import Window  # nuitka, do not delete
import glcontext  # do not delete

from ImNodeEditor import NE
from ImNodeEditor import Node

from gui import my_node_editor


class WindowEvents(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "imgui Integration"
    aspect_ratio = None
    vsync = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        imgui.create_context()
        io = imgui.get_io()

        font_size = 16
        font_scale = 0.75  # 越小约清晰
        self.font = io.fonts.add_font_from_file_ttf(
            './resources/fonts/arial.ttf', font_size / font_scale, glyph_ranges=io.fonts.get_glyph_ranges_chinese_full())
        self.font_bold = io.fonts.add_font_from_file_ttf(
            './resources/fonts/arialbd.ttf', font_size / font_scale,
            glyph_ranges=io.fonts.get_glyph_ranges_chinese_full())
        io.font_global_scale = font_scale
        self.imgui = ModernglWindowRenderer(self.wnd)

        NE.set_window_event(self)

    def render(self, time: float, frametime: float):
        Node.main_loop()  # Node :: main loop
        self.render_ui()

    def render_ui(self):
        imgui.new_frame()
        with imgui.font(self.font):
            imgui.show_test_window()

            # begin window
            flags = imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
            imgui.set_next_window_position(0, 0)
            imgui.set_next_window_size(*self.wnd.size)
            imgui.begin('My Node Editor Window', flags=flags)
            if imgui.button('save'): Node.save('./node_file.bin')
            imgui.same_line()
            if imgui.button('load'): Node.load('./node_file.bin')
            imgui.same_line()
            if imgui.button('edit pin colors'): imgui.open_popup('pin color editor')
            if imgui.begin_popup('pin color editor'):
                my_node_editor.show_pin_color_editor()
                if imgui.button('copy code'): my_node_editor.copy_pin_colors()
                imgui.end_popup()
            imgui.same_line()
            if imgui.button('edit node colors'): imgui.open_popup('node color editor')
            if imgui.begin_popup('node color editor'):
                my_node_editor.show_node_color_editor()
                if imgui.button('copy code'): my_node_editor.copy_node_colors()
                imgui.end_popup()
            imgui.same_line()
            imgui.text(f'{(1 / NE.FRAME_TIME):.0f} fps')
            NE.begin()  # NE :: begin node editor canvas
            Node.draw_all_nodes()  # Node :: draw all nodes
            NE.end()  # NE :: end node editor canvas

            imgui.end()  # end window

        imgui.render()
        self.imgui.render(imgui.get_draw_data())

    def resize(self, width: int, height: int):
        self.imgui.resize(width, height)

    def key_event(self, key, action, modifiers):
        self.imgui.key_event(key, action, modifiers)
        NE.handle_key_event(key, action, modifiers)

    def mouse_position_event(self, x, y, dx, dy):
        self.imgui.mouse_position_event(x, y, dx, dy)
        NE.handle_mouse_position_event(x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        self.imgui.mouse_drag_event(x, y, dx, dy)
        NE.handle_mouse_drag_event(x, y, dx, dy)

    def mouse_scroll_event(self, x_offset, y_offset):
        self.imgui.mouse_scroll_event(x_offset, y_offset)
        NE.handle_mouse_scroll_event(x_offset, y_offset)

    def mouse_press_event(self, x, y, button):
        self.imgui.mouse_press_event(x, y, button)
        NE.handle_mouse_press_event(x, y, button)

    def mouse_release_event(self, x: int, y: int, button: int):
        self.imgui.mouse_release_event(x, y, button)
        NE.handle_mouse_release_event(x, y, button)

    def unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)


if __name__ == '__main__':
    mglw.run_window_config(WindowEvents)
