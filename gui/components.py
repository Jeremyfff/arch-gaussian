import os
import time
from enum import Enum
from typing import Callable

import imgui
from moderngl import Texture

from gui import global_var as g
from gui.modules import StyleModule
from gui.modules import texture_module
from gui.utils import color_utils
from scripts.project_manager import ProjectManager


def icon_button(icon_name, width=None, height=None, uv0=(0, 0), uv1=(1, 1), tint_color=(1, 1, 1, 1),
                border_color=(0, 0, 0, 0), bg_color=(0, 0, 0, 0), tooltip=None, id=None) -> bool:
    tint_color = color_utils.align_alpha(tint_color, g.mImguiStyle.colors[imgui.COLOR_BUTTON])
    rounding = g.mImguiStyle.frame_rounding
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


def bold_text(content):
    with imgui.font(g.mFontBold):
        imgui.text(content)


def gray_text(content):
    imgui.set_window_font_scale(0.8)
    gray_color = color_utils.align_alpha(StyleModule.COLOR_GRAY, g.mImguiStyle.colors[imgui.COLOR_TEXT])
    imgui.push_style_color(imgui.COLOR_TEXT, *gray_color)
    imgui.text(content)
    imgui.pop_style_color()
    imgui.set_window_font_scale(1.0)


def icon_image(icon_name, width=None, height=None, uv0=(0, 0), uv1=(1, 1), tint_color=(1, 1, 1, 1),
               border_color=(0, 0, 0, 0), padding=False):
    tint_color = color_utils.align_alpha(tint_color, g.mImguiStyle.colors[imgui.COLOR_TEXT])
    icon_height = imgui.get_frame_height() if height is None else height
    if padding:
        icon_height -= g.mImguiStyle.frame_padding[1] * 2
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
    begin_child(name, width, height, border=False)
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
    gray_color = color_utils.align_alpha(StyleModule.COLOR_GRAY, g.mImguiStyle.colors[imgui.COLOR_TEXT])
    imgui.push_style_color(imgui.COLOR_TEXT, *gray_color)
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


def easy_question_mark(content):
    imgui.same_line()
    imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + g.mImguiStyle.frame_padding[1])
    icon_image('question-line', padding=True, tint_color=(0.5, 0.5, 0.5, 0.5))
    easy_tooltip(content)


def image_gallery(name, texture_infos: dict[str:Texture], width=0.0, height=0.0, columns=4):
    imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, 0, 0, 0, 0)
    begin_child(f'image_gallery_{name}', width, height, border=True)
    tint_color = color_utils.align_alpha(StyleModule.COLOR_WHITE, g.mImguiStyle.colors[imgui.COLOR_TEXT])
    with imgui.begin_table(f'table_{name}', columns):
        imgui.table_next_column()
        for texture_name, texture in texture_infos.items():
            ratio = texture.width / texture.height
            width = imgui.get_content_region_available_width()
            height = int(width / ratio)
            imgui.image(texture.glo, width, height, (0, 0), (1, 1), tint_color)
            imgui.text(texture_name)
            imgui.table_next_column()
    imgui.end_child()
    imgui.pop_style_color()


def image_gallery_with_title(title, folder_path, processing_flag=False, last_add_time=None,
                             last_add_time_callback=None):
    """
    包括自动更新功能
    title: 标题
    folder_path: 要查找的文件夹
    processing_flag: 是否正在处理，如果为真，则将自动启用add mode
    last_add_time: 上次刷新的时间
    last_add_time_callback: 接受一个参数，修改上次刷新的时间
    """
    imgui.push_id(title)
    imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + g.mImguiStyle.frame_padding[1])
    bold_text(title)
    easy_tooltip(folder_path)
    imgui.same_line()
    imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() - g.mImguiStyle.frame_padding[1])
    imgui.set_cursor_pos_x(
        imgui.get_cursor_pos_x() + imgui.get_content_region_available_width() - imgui.get_frame_height())
    force_update = icon_button('refresh-line')
    add_mode = False
    if last_add_time is not None:
        if time.time() - last_add_time > 1:
            add_mode = processing_flag
            if last_add_time_callback is not None:
                last_add_time_callback(time.time())
    thumbnail_info = texture_module.get_folder_thumbnails(
        folder_path,
        icon_size=int(imgui.get_content_region_available_width() / 4),
        force_update=force_update,
        add_mode=add_mode
    )  # {name : Texture}
    image_gallery(title, thumbnail_info,
                  width=imgui.get_content_region_available_width(),
                  height=imgui.get_content_region_available_width() / 2,
                  columns=4)
    imgui.pop_id()


_cached_confirm_create_project_path = ''


def create_project_confirm_popup(open_flag, path):
    global _cached_confirm_create_project_path
    if open_flag:
        imgui.open_popup('confirm_create_project')
        _cached_confirm_create_project_path = path
    if imgui.is_popup_open('confirm_create_project'):
        imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 8)
    if imgui.begin_popup_modal('confirm_create_project', True,
                               imgui.WINDOW_ALWAYS_AUTO_RESIZE | imgui.WINDOW_NO_TITLE_BAR).opened:
        imgui.text('Cannot find project at: ')
        imgui.push_style_color(imgui.COLOR_TEXT, *StyleModule.COLOR_GRAY)
        imgui.set_window_font_scale(0.8)
        imgui.text(_cached_confirm_create_project_path)
        imgui.set_window_font_scale(1.0)
        imgui.pop_style_color()
        imgui.text('Do you want to create project at this location?')
        if imgui.button('YES'):
            ProjectManager.create_project(
                os.path.basename(_cached_confirm_create_project_path), _cached_confirm_create_project_path
            )
            imgui.close_current_popup()
        imgui.same_line()
        if imgui.button('NO'):
            imgui.close_current_popup()

        imgui.end_popup()
        imgui.pop_style_var()


def begin_child(name, width=0, height=0, border=True, flags=imgui.WINDOW_NONE):
    imgui.begin_child(name, width, height, border=border, flags=flags)


def quick_menu_item(label, callback=None):
    clicked, state = imgui.menu_item(label)
    if clicked:
        if callback is not None:
            callback()


class ArgType(Enum):
    NONE = -1
    INTEGER = 0
    FLOAT = 1
    STRING = 2
    PATH = 3
    BOOLEAN = 4
    DICT = 5
    FLOAT2 = 6
    INT2 = 7
    FOLDER = 8
    OPTIONAL_INT = 9


def get_arg_types(args: dict):
    arg_types_dict = {}
    for key in args.keys():
        value = args[key]
        if isinstance(value, bool):
            arg_types_dict[key] = ArgType.BOOLEAN
            continue
        if isinstance(value, int):
            arg_types_dict[key] = ArgType.INTEGER
            continue
        if isinstance(value, float):
            arg_types_dict[key] = ArgType.FLOAT
            continue
        if isinstance(value, str):
            if 'path' in key.lower() or 'executable' in key.lower() or os.path.isfile(value):
                arg_types_dict[key] = ArgType.PATH
                continue
            if 'folder' in key.lower() or os.path.isdir(value):
                arg_types_dict[key] = ArgType.FOLDER
                continue
            arg_types_dict[key] = ArgType.STRING
            continue
        if value is None:
            arg_types_dict[key] = ArgType.NONE
            continue
        if isinstance(value, dict):
            arg_types_dict[key] = ArgType.DICT
            continue
        if isinstance(value, tuple):
            if len(value) == 2:
                if isinstance(value[0], int):
                    arg_types_dict[key] = ArgType.INT2
                    continue
                if isinstance(value[0], float):
                    arg_types_dict[key] = ArgType.FLOAT2
                    continue
        raise Exception(f'遇到了不能识别的类型{value}, type={type(value)}，请检查arg的{key}数据')
    return arg_types_dict


def arg_editor(args: dict, arg_type_dict: dict, disabled_keys: set = None, hidden_keys: set = None,
               custom_lines: dict[any:Callable] = None):
    from gui.utils import io_utils
    width = imgui.get_content_region_available_width() / 2
    style: imgui.core.GuiStyle = imgui.get_style()

    if disabled_keys is None:
        disabled_keys = set()
    if hidden_keys is None:
        hidden_keys = set()
    if custom_lines is None:
        custom_lines = {}
    any_change = False
    org_keys = list(args.keys())  # arg.keys的size可能会在运行时改变
    for key in org_keys:
        if key.startswith('$'):
            # 跳过一些特殊key
            continue
        if key in hidden_keys:
            # 被隐藏
            continue
        if key in custom_lines:
            # 自定义的line， 需要返回changed 和 value
            changed, args[key] = custom_lines[key]()
            continue
        if key in disabled_keys:
            # 被禁用的line
            imgui.push_style_color(imgui.COLOR_TEXT, *StyleModule.COLOR_GRAY)
            imgui.set_next_item_width(width)
            imgui.input_text(key, args[key], -1, imgui.INPUT_TEXT_READ_ONLY)
            imgui.pop_style_color()
            continue
        tp: ArgType = arg_type_dict[key]
        if tp == ArgType.INTEGER:
            imgui.set_next_item_width(width)
            changed, args[key] = imgui.input_int(key, args[key])
            any_change |= changed
            continue
        if tp == ArgType.FLOAT:
            imgui.set_next_item_width(width)
            changed, args[key] = imgui.input_float(key, args[key], format='%.5f')
            any_change |= changed
            continue
        if tp == ArgType.BOOLEAN:
            imgui.set_next_item_width(width)
            changed, args[key] = imgui.checkbox(key, args[key])
            any_change |= changed
            continue
        if tp == ArgType.STRING:
            imgui.set_next_item_width(width)
            changed, args[key] = imgui.input_text(key, args[key])
            any_change |= changed
            continue
        if tp == ArgType.PATH:
            imgui.set_next_item_width(width - 45 * g.GLOBAL_SCALE - style.item_spacing[0])
            imgui.push_id(key)
            changed, args[key] = imgui.input_text('', args[key])
            any_change |= changed
            imgui.same_line()
            if imgui.button('...', width=45 * g.GLOBAL_SCALE):
                args[key] = io_utils.open_file_dialog()
                any_change |= True
            imgui.pop_id()
            imgui.same_line()
            imgui.text(key)
            continue
        if tp == ArgType.FOLDER:
            imgui.set_next_item_width(width - 45 * g.GLOBAL_SCALE - style.item_spacing[0])
            imgui.push_id(key)
            changed, args[key] = imgui.input_text('', args[key])
            any_change |= changed
            imgui.same_line()
            if imgui.button('...', width=45 * g.GLOBAL_SCALE):
                args[key] = io_utils.open_folder_dialog()
                any_change |= True
            imgui.pop_id()
            imgui.same_line()
            imgui.text(key)
        if tp == ArgType.FLOAT2:
            imgui.set_next_item_width(width)
            changed, args[key] = imgui.input_float2(key, *args[key])
            any_change |= changed
            continue
        if tp == ArgType.INT2:
            imgui.set_next_item_width(width)
            changed, args[key] = imgui.input_int2(key, *args[key])
            any_change |= changed
            continue
        if tp == ArgType.OPTIONAL_INT:
            imgui.push_id(key)
            state_key = f'${key}_enabled'
            value_key = f'${key}_value'
            if state_key not in args.keys():
                # 初始化
                args[state_key] = args[key] is not None
            if value_key not in args.keys():
                # 初始化
                args[value_key] = args[key] if args[key] is not None else 0
            imgui.set_next_item_width(45 * g.GLOBAL_SCALE)
            changed, args[state_key] = imgui.checkbox('', args[state_key])
            any_change |= changed
            if args[state_key]:
                imgui.same_line()
                imgui.set_next_item_width(width - imgui.get_cursor_pos_x())
                changed, args[value_key] = imgui.input_int(key, args[value_key])
                any_change |= changed
            else:
                imgui.same_line()
                imgui.text(key)
            if any_change:
                args[key] = args[value_key] if args[state_key] else None
            imgui.pop_id()
    return any_change
