from typing import Callable

from gui import global_var as g
import imgui
from gui.modules import texture_module


def icon_button(icon_name, width=None, height=None, uv0=(0, 0), uv1=(1, 1), tint_color=(1, 1, 1, 1),
                border_color=(0, 0, 0, 0), bg_color=(0, 0, 0, 0), tooltip=None, id=None) -> bool:
    rounding = 4
    icon_height = imgui.get_frame_height() if height is None else height
    icon_height -= rounding * 2
    icon_width = icon_height if width is None else width
    imgui.push_style_color(imgui.COLOR_BUTTON, *bg_color)
    imgui.push_style_var(imgui.STYLE_FRAME_PADDING, (rounding, rounding))
    if id is not None:
        imgui.push_id(str(id))
    clicked = imgui.image_button(texture_module.get_icon(icon_name), icon_width, icon_height, uv0, uv1, tint_color,
                                 border_color, -1)
    if id is not None:
        imgui.pop_id()
    imgui.pop_style_color()
    imgui.pop_style_var()
    easy_tooltip(tooltip)

    return clicked


def icon_image(icon_name, width=None, height=None, uv0=(0, 0), uv1=(1, 1), tint_color=(1, 1, 1, 1),
               border_color=(0, 0, 0, 0)):
    icon_height = imgui.get_frame_height() if height is None else height
    icon_width = icon_height if width is None else width
    imgui.image(texture_module.get_icon(icon_name), icon_width, icon_height, uv0, uv1, tint_color, border_color)


_selectable_region_hovering_data = {}


def selectable_region(name, width, height, content: Callable, *args):
    if name not in _selectable_region_hovering_data:
        _selectable_region_hovering_data[name] = False
        is_hovering = False
    else:
        is_hovering = _selectable_region_hovering_data[name]
    clicked = False
    if is_hovering:
        if imgui.is_mouse_released(0):
            imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, *g.mImguiStyle.colors[imgui.COLOR_BUTTON_ACTIVE])
            clicked = True
        elif imgui.is_mouse_down(0):
            imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, *g.mImguiStyle.colors[imgui.COLOR_BUTTON_ACTIVE])
        else:
            imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, *g.mImguiStyle.colors[imgui.COLOR_BUTTON_HOVERED])
    else:
        imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, *g.mImguiStyle.colors[imgui.COLOR_BUTTON])
    imgui.push_style_var(imgui.STYLE_CHILD_ROUNDING, g.mImguiStyle.frame_rounding)
    imgui.begin_child(name, width, height, border=False)
    if not clicked:
        _selectable_region_hovering_data[name] = imgui.is_window_hovered()
    else:
        _selectable_region_hovering_data[name] = False
    content(*args)
    imgui.end_child()
    imgui.pop_style_color()
    imgui.pop_style_var()
    return clicked


def _draw_icon_and_text(icon, text):
    pos = imgui.get_cursor_pos()
    imgui.set_cursor_pos((pos[0] + g.mImguiStyle.frame_padding[0], pos[1] + g.mImguiStyle.frame_padding[1]))
    size = imgui.get_frame_height() - g.mImguiStyle.frame_padding[1] * 2
    icon_image(icon, size, size)
    imgui.same_line()
    imgui.text(text)


def icon_text_button(icon, text, width=None, height=None):
    if width is None:
        width = imgui.calc_text_size(text)[0] + imgui.get_frame_height() + \
                g.mImguiStyle.item_spacing[0]
    if height is None:
        height = imgui.get_frame_height()
    return selectable_region(f'icon_text_button_{icon}_{text}', width, height, _draw_icon_and_text, icon, text)


_text2_color = (0.6, 0.6, 0.6, 1.0)


def _draw_icon_and_double_text(icon, text1, text2):
    pos = imgui.get_cursor_pos()
    imgui.set_cursor_pos((pos[0] + g.mImguiStyle.frame_padding[0], pos[1] + g.mImguiStyle.frame_padding[1]))
    size = imgui.get_frame_height() - g.mImguiStyle.frame_padding[1] * 1  # (-2 + 1) = 1 make icon bigger
    imgui.begin_group()
    icon_image(icon, size, size)
    imgui.end_group()
    imgui.same_line()
    imgui.begin_group()
    imgui.text(text1)
    imgui.push_style_color(imgui.COLOR_TEXT, *_text2_color)
    imgui.set_window_font_scale(0.8)
    imgui.text(text2)
    imgui.set_window_font_scale(1.0)
    imgui.pop_style_color()
    imgui.end_group()


def icon_double_text_button(icon, text1, text2, width=None, height=None):
    if width is None:
        text1_size = imgui.calc_text_size(text1)
        text2_size = imgui.calc_text_size(text2)
        max_text_width = max(text2_size[0], text1_size[0])
        width = max_text_width + imgui.get_frame_height() + g.mImguiStyle.item_spacing[0] + g.mImguiStyle.frame_padding[
            0] * 1  # frame padding = icon(-2 + 1) + border 2 = 1
    if height is None:
        height = g.FONT_SIZE * 2 + g.mImguiStyle.item_spacing[1] + g.mImguiStyle.frame_padding[1] * 2
    return selectable_region(f'icon_text_button_{icon}_{text1}_{text2}', width, height, _draw_icon_and_double_text,
                             icon,
                             text1, text2)


def easy_tooltip(content):
    if content is None or content == '':
        return
    if imgui.is_item_hovered():
        imgui.set_tooltip(content)
