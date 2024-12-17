import imgui

from gui.components import c
from gui.global_app_state import g
from gui.modules import StyleModule
from gui.windows.base_window import PopupWindow

"""
put all popup modal windows here
"""


class ConfirmCloseWindow(PopupWindow):
    _name = 'ConfirmCloseWindow'
    _flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_SCROLL_WITH_MOUSE | imgui.WINDOW_NO_SCROLLBAR



    @classmethod
    def w_init(cls):
        super().w_init()

    @classmethod
    def w_update(cls):
        super().w_update()


    @classmethod
    def w_open(cls):
        super().w_open()
        from gui.windows import POPUP_WINDOWS
        for window in POPUP_WINDOWS:
            if window.is_opened():
                window.w_close()

    @classmethod
    def w_close(cls):
        super().w_close()

    @classmethod
    def w_before_window_begin(cls):
        imgui.set_next_window_position(0, 0)
        imgui.set_next_window_size(*g.mWindowSize)

    @classmethod
    def w_content(cls):
        super().w_content()
        # tex = g.mWindowManager.get_blur_texture()
        # imgui.set_cursor_pos_x(0)
        # imgui.set_cursor_pos_y(0)
        #
        # imgui.image(tex.glo, *imgui.get_window_size(), (0, 1), (1, 0))

        imgui.push_style_var(imgui.STYLE_FRAME_ROUNDING, g.mImguiStyle.frame_rounding * 3)
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, (g.mImguiStyle.frame_padding[0], g.mImguiStyle.frame_padding[1] * 2))
        imgui.set_cursor_pos_y(g.mWindowSize[1] * 0.5 - (imgui.get_frame_height_with_spacing() * 2) * 0.5)
        text_content = "Are you sure to exit? "
        text_size = imgui.calc_text_size(text_content)
        imgui.set_cursor_pos_x(g.mWindowSize[0] * 0.5 - text_size[0] * 0.5)
        imgui.text(text_content)

        imgui.dummy(width=0, height=20 * g.global_scale)

        imgui.set_cursor_pos_x(g.mWindowSize[0] * 0.5 - (400 * g.global_scale + g.mImguiStyle.item_spacing[0]) * 0.5)
        imgui.push_style_color(imgui.COLOR_BUTTON, *StyleModule.COLOR_PRIMARY)
        if c.icon_text_button("checkbox-circle-line", "YES", width=200 * g.global_scale, height=None, align_center=True):
            g.mConfirmClose = True
            cls.w_close()
        imgui.pop_style_color()
        imgui.same_line()
        imgui.push_style_color(imgui.COLOR_BUTTON, *StyleModule.COLOR_SECONDARY)
        if c.icon_text_button("close-circle-line", "CANCEL", width=200 * g.global_scale, height=None, align_center=True):
            g.mIsClosing = False
            cls.w_close()
        imgui.pop_style_color()
        imgui.pop_style_var(2)

    @classmethod
    def w_after_window_end(cls):
        pass
