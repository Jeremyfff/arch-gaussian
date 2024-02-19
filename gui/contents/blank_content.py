import imgui

from gui import global_var as g
from gui import components as c
from gui.modules import style_module
welcome_text = """ Introducing the all-new EchoSphere Smart Speaker – your gateway to a seamless smart home experience.
Experience the power of voice control with EchoSphere, your personal assistant that responds to your every command. From playing your favorite music to setting reminders and controlling smart devices, EchoSphere is designed to make your life easier and more convenient.
With its sleek and modern design, EchoSphere seamlessly blends into any room decor, adding a touch of sophistication to your living space. Its advanced sound technology ensures crystal-clear audio for an immersive listening experience.
"""


def show():
    window_width = imgui.get_window_width()
    window_height = imgui.get_window_height()
    content_width = 600 * g.GLOBAL_SCALE
    content_height = 300 * g.GLOBAL_SCALE
    start_x = (window_width - content_width) / 2
    start_y = (window_height - content_height) / 2
    imgui.set_cursor_pos((start_x, start_y))
    imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, 0, 0, 1,0)
    imgui.begin_child('welcome', content_width, content_height, border=False)
    flags = imgui.WINDOW_NO_SCROLLBAR
    inner_width = content_width / 2 - g.mImguiStyle.window_padding[0] - g.mImguiStyle.item_spacing[0]/2
    inner_height = content_height - 2 * g.mImguiStyle.window_padding[1]
    imgui.begin_child('left', inner_width - 20 * g.GLOBAL_SCALE, inner_height, border=False, flags=flags)
    imgui.push_style_color(imgui.COLOR_TEXT, *style_module.gray)
    imgui.text_wrapped(welcome_text)
    imgui.pop_style_color()
    imgui.end_child()
    imgui.same_line()
    imgui.set_cursor_pos_x(imgui.get_cursor_pos_x() + 20 * g.GLOBAL_SCALE)
    imgui.begin_child('right', inner_width, inner_height, border=False, flags=flags)
    imgui.push_style_var(imgui.STYLE_ITEM_SPACING, (4, 10*g.GLOBAL_SCALE))
    imgui.push_style_var(imgui.STYLE_FRAME_PADDING, (g.mImguiStyle.frame_padding[0]*2, g.mImguiStyle.window_padding[1] * 2))

    with imgui.font(g.mFontBold):
        imgui.text('ARCH GAUSSIAN V0.1')
    imgui.text('')
    imgui.text('')
    imgui.text('')
    c.icon_text_button('folder-add-line', 'New Project...', imgui.get_content_region_available_width())
    c.icon_text_button('folder-open-line', 'Open Project...', imgui.get_content_region_available_width())
    imgui.separator()
    c.icon_text_button('git-repository-line', 'Open Repository...', imgui.get_content_region_available_width())
    imgui.pop_style_var(2)
    imgui.end_child()
    imgui.end_child()
    imgui.pop_style_color()

