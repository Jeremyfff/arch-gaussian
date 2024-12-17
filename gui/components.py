import logging
import os
import time
from typing import Callable, Union

import imgui
from moderngl import Texture

from gui import modules  # 这里不要导入具体的module， 就可以解决循环引用的问题。可以在具体的modules中导入components
from gui.global_app_state import g
from gui.utils import arg_utils, io_utils, color_utils
from scripts.project_manager import ProjectManager

__runtime__ = True
if not __runtime__:
    from gui.modules.graphic_module import RoundedButtonFBT, ProgressBarFBT


class Components:
    @staticmethod
    def icon_button(icon_name, width=None, height=None, uv0=(0, 0), uv1=(1, 1), tint_color=(1, 1, 1, 1),
                    border_color=(0, 0, 0, 0), bg_color=(0, 0, 0, 0), tooltip=None, id=None) -> bool:
        tint_color = color_utils.align_alpha(tint_color, g.mImguiStyle.colors[imgui.COLOR_BUTTON])
        rounding = g.mImguiStyle.frame_rounding
        icon_height = imgui.get_frame_height() if height is None else height
        icon_width = icon_height if width is None else width
        icon_height -= rounding * 2
        icon_width -= rounding * 2
        imgui.push_style_color(imgui.COLOR_BUTTON, *bg_color)
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, (rounding, rounding))
        if id is not None:
            imgui.push_id(str(id))
        clicked = imgui.image_button(modules.TextureModule.get_icon_glo(icon_name), icon_width, icon_height, uv0, uv1, tint_color,
                                     border_color, -1)
        if id is not None:
            imgui.pop_id()
        imgui.pop_style_color(1)
        imgui.pop_style_var(1)
        Components.easy_tooltip(tooltip)

        return clicked

    @staticmethod
    def image_button(texture_name, width=None, height=None, uv0=(0, 0), uv1=(1, 1), tint_color=(1, 1, 1, 1),
                     border_color=(0, 0, 0, 0), bg_color=(0, 0, 0, 0), tooltip=None, id=None) -> bool:
        glo = modules.TextureModule.get_texture_glo(texture_name)
        return Components.image_button_using_glo(glo, width, height, uv0, uv1, tint_color, border_color, bg_color, tooltip, id)

    @staticmethod
    def image_button_using_glo(texture_glo, width=None, height=None, uv0=(0, 0), uv1=(1, 1), tint_color=(1, 1, 1, 1),
                               border_color=(0, 0, 0, 0), bg_color=(0, 0, 0, 0), tooltip=None, id=None) -> bool:
        tint_color = color_utils.align_alpha(tint_color, g.mImguiStyle.colors[imgui.COLOR_BUTTON])
        rounding = g.mImguiStyle.frame_rounding
        icon_height = imgui.get_frame_height() if height is None else height
        icon_width = icon_height if width is None else width
        icon_height -= rounding * 2
        icon_width -= rounding * 2
        imgui.push_style_color(imgui.COLOR_BUTTON, *bg_color)
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, (rounding, rounding))
        if id is not None:
            imgui.push_id(str(id))
        clicked = imgui.image_button(texture_glo, icon_width, icon_height, uv0, uv1, tint_color,
                                     border_color, -1)
        if id is not None:
            imgui.pop_id()
        imgui.pop_style_color(1)
        imgui.pop_style_var(1)
        Components.easy_tooltip(tooltip)

        return clicked

    @staticmethod
    def _move_cursor_to_center_by_text_size(content: str):
        width = imgui.get_content_region_available()[0]
        text_width = imgui.calc_text_size(content)[0]
        x = imgui.get_cursor_pos_x()
        indent = (width - text_width) / 2
        imgui.set_cursor_pos_x(x + indent)

    @staticmethod
    def _move_cursor_to_center_by_button_width(button_width):
        width = imgui.get_content_region_available()[0]
        x = imgui.get_cursor_pos_x()
        indent = (width - button_width) / 2
        imgui.set_cursor_pos_x(x + indent)

    @staticmethod
    def text(content, center=False):
        if center:
            Components._move_cursor_to_center_by_text_size(content)
        imgui.text(content)

    @staticmethod
    def bold_text(content, center=False):
        with imgui.font(g.mFontBold):
            if center:
                Components._move_cursor_to_center_by_text_size(content)
            imgui.text(content)

    @staticmethod
    def gray_text(content, center=False):
        imgui.set_window_font_scale(0.8)
        if center:
            Components._move_cursor_to_center_by_text_size(content)
        gray_color = color_utils.align_alpha(modules.StyleModule.COLOR_GRAY, g.mImguiStyle.colors[imgui.COLOR_TEXT])
        imgui.push_style_color(imgui.COLOR_TEXT, *gray_color)
        imgui.text(content)
        imgui.pop_style_color()
        imgui.set_window_font_scale(1.0)

    @staticmethod
    def warning_text(content, center=False):
        if center:
            Components._move_cursor_to_center_by_text_size(content)
        color = color_utils.align_alpha(modules.StyleModule.COLOR_WARNING, g.mImguiStyle.colors[imgui.COLOR_TEXT])
        imgui.push_style_color(imgui.COLOR_TEXT, *color)
        imgui.text(content)
        imgui.pop_style_color()

    @staticmethod
    def highlight_text(content, center=False):
        if center:
            Components._move_cursor_to_center_by_text_size(content)
        color = color_utils.align_alpha(modules.StyleModule.COLOR_PRIMARY, g.mImguiStyle.colors[imgui.COLOR_TEXT])
        imgui.push_style_color(imgui.COLOR_TEXT, *color)
        imgui.text(content)
        imgui.pop_style_color()

    @staticmethod
    def icon_image(icon_name, width=None, height=None, uv0=(0, 0), uv1=(1, 1), tint_color=(1, 1, 1, 1),
                   border_color=(0, 0, 0, 0), padding=False):
        tint_color = color_utils.align_alpha(tint_color, g.mImguiStyle.colors[imgui.COLOR_TEXT])
        icon_height = imgui.get_frame_height() if height is None else height
        if padding:
            icon_height -= g.mImguiStyle.frame_padding[1] * 2
        icon_width = icon_height if width is None else width
        imgui.image(modules.TextureModule.get_icon_glo(icon_name), icon_width, icon_height, uv0, uv1, tint_color, border_color)

    _selectable_region_hovering_data: dict[str: bool] = {}

    @staticmethod
    def selectable_region(uid, width: Union[int, float], height: Union[int, float], content: Callable, *args):
        width = int(width)
        height = int(height)
        if uid not in Components._selectable_region_hovering_data:
            Components._selectable_region_hovering_data[uid] = False
            is_hovering = False
        else:
            is_hovering = Components._selectable_region_hovering_data[uid]

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
        Components.begin_child(uid, width, height, border=False)
        # region advanced drawing
        Components._advanced_drawing_for_selectable_region(uid, width, height, is_hovering)
        # endregion
        if not clicked:
            Components._selectable_region_hovering_data[uid] = imgui.is_window_hovered()
        else:
            Components._selectable_region_hovering_data[uid] = False
        content(*args)
        imgui.end_child()
        imgui.pop_style_color(1)
        imgui.pop_style_var(1)
        return clicked

    _selectable_region_animation_data: dict[str: float] = {}
    _selectable_region_fbt_data: dict[str: "RoundedButtonFBT"] = {}

    @staticmethod
    def _advanced_drawing_for_selectable_region(name, width, height, is_hovering):

        if g.mIsHandlingBlurCommand:
            # 正在进行模糊渲染时，不渲染高级效果
            return
        if width <= 0 or height <= 0:
            # 如果宽度高度非法，不渲染
            return
        if name not in Components._selectable_region_animation_data:
            Components._selectable_region_animation_data[name] = 0

        if name not in Components._selectable_region_fbt_data:
            Components._selectable_region_fbt_data[name] = modules.graphic_module.RoundedButtonFBT(width, height)

        _fbt: "RoundedButtonFBT" = Components._selectable_region_fbt_data[name]
        if _fbt.width != width or _fbt.height != height:
            _fbt.update_size(width, height)

        _T = Components._selectable_region_animation_data[name]
        _target = 1.0 if is_hovering else 0.0
        _delta = _target - _T
        _p = min(1.0, g.mFrametime * 7.0)  # speed
        _p = _p * 0.5 if _delta < 0 else _p  # slow down when disappear
        _delta *= _p
        if _delta == 0:
            return
        _T += _delta
        Components._selectable_region_animation_data[name] = _T

        _fbt.render(_T, rounding=g.mImguiStyle.frame_rounding)
        _w_pos = imgui.get_window_position()
        _w_size = imgui.get_window_size()
        modules.DrawingModule.draw_image(
            _fbt.texture_id,
            _w_pos[0],
            _w_pos[1],
            _w_pos[0] + _w_size[0],
            _w_pos[1] + _w_size[1],
            draw_list_type="window",
            col=color_utils.lighten_color(g.mImguiStyle.colors[imgui.COLOR_BUTTON_HOVERED], 0.1)
        )

    @staticmethod
    def _draw_icon_and_text(icon, text, text_width, align_center):
        pos = imgui.get_cursor_pos()
        imgui.set_cursor_pos((pos[0] + g.mImguiStyle.frame_padding[0], pos[1] + g.mImguiStyle.frame_padding[1]))
        size = imgui.get_frame_height() - g.mImguiStyle.frame_padding[1] * 2
        Components.icon_image(icon, size, size)
        imgui.same_line()
        if align_center:
            indent = (imgui.get_content_region_available_width() - text_width) / 2
            imgui.set_cursor_pos_x(imgui.get_cursor_pos_x() + indent)
        imgui.text(text)

    @staticmethod
    def button(text, width=None, height=None, button_align_center=False, text_align_center=False, uid=None):
        text_width = imgui.calc_text_size(text)[0]
        if width is None:
            width = text_width + g.mImguiStyle.frame_padding[0] * 2
        if height is None:
            height = imgui.get_frame_height()
        if button_align_center:
            Components._move_cursor_to_center_by_button_width(width)
        return Components.selectable_region(uid if uid is not None else f'button_{text}', width, height,
                                            Components._draw_text_inner_selectable_region, text, text_align_center)

    @staticmethod
    def _draw_text_inner_selectable_region(text, center=False):
        # align y
        if center:
            text_height = imgui.calc_text_size(text)[1]
            wnd_height = imgui.get_window_height()
            y = (wnd_height - text_height) / 2
            imgui.set_cursor_pos((g.mImguiStyle.frame_padding[0], y))

        Components.text(text, center)  # the center here only controls x-axis

    @staticmethod
    def icon_text_button(icon, text, width=None, height=None, align_center=False, uid=None):
        text_width = imgui.calc_text_size(text)[0]
        if width is None:
            width = text_width + imgui.get_frame_height() + \
                    g.mImguiStyle.item_spacing[0]
        if height is None:
            height = imgui.get_frame_height()

        return Components.selectable_region(uid if uid is not None else f'icon_text_button_{icon}_{text}', width, height,
                                            Components._draw_icon_and_text, icon, text,
                                            text_width, align_center)

    @staticmethod
    def _draw_icon_and_double_text(icon, text1, text2):
        pos = imgui.get_cursor_pos()
        imgui.set_cursor_pos((pos[0] + g.mImguiStyle.frame_padding[0], pos[1] + g.mImguiStyle.frame_padding[1]))
        size = imgui.get_frame_height() - g.mImguiStyle.frame_padding[1] * 1  # (-2 + 1) = 1 make icon bigger
        imgui.begin_group()
        Components.icon_image(icon, size, size)
        imgui.end_group()
        imgui.same_line()
        imgui.begin_group()
        imgui.text(text1)
        gray_color = color_utils.align_alpha(modules.StyleModule.COLOR_GRAY, g.mImguiStyle.colors[imgui.COLOR_TEXT])
        imgui.push_style_color(imgui.COLOR_TEXT, *gray_color)
        imgui.set_window_font_scale(0.8)
        imgui.text(text2)
        imgui.set_window_font_scale(1.0)
        imgui.pop_style_color()
        imgui.end_group()

    @staticmethod
    def icon_double_text_button(icon, text1, text2, width=None, height=None, uid=None):
        if width is None:
            text1_size = imgui.calc_text_size(text1)
            text2_size = imgui.calc_text_size(text2)
            max_text_width = max(text2_size[0], text1_size[0])
            width = max_text_width + imgui.get_frame_height() + g.mImguiStyle.item_spacing[0] + g.mImguiStyle.frame_padding[
                0] * 1  # frame padding = icon(-2 + 1) + border 2 = 1
        if height is None:
            height = Components.get_icon_double_text_button_height()
        return Components.selectable_region(uid if uid is not None else f'icon_text_button_{icon}_{text1}_{text2}', width, height, Components._draw_icon_and_double_text,
                                            icon,
                                            text1, text2)

    @staticmethod
    def get_icon_double_text_button_height():
        return g.font_size * 2 + g.mImguiStyle.item_spacing[1] + g.mImguiStyle.frame_padding[1] * 2

    @staticmethod
    def easy_tooltip(content):
        if content is None or content == '':
            return
        if imgui.is_item_hovered():
            imgui.set_tooltip(content)

    @staticmethod
    def easy_question_mark(content):
        imgui.same_line()
        imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + g.mImguiStyle.frame_padding[1])
        Components.icon_image('question-line', padding=True, tint_color=(0.5, 0.5, 0.5, 0.5))
        Components.easy_tooltip(content)

    @staticmethod
    def image_gallery(name, texture_infos: dict[str:Texture], width=0.0, height=0.0, columns=4):
        imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, 0, 0, 0, 0)
        Components.begin_child(f'image_gallery_{name}', width, height, border=True)
        tint_color = color_utils.align_alpha(modules.StyleModule.COLOR_WHITE, g.mImguiStyle.colors[imgui.COLOR_TEXT])
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

    @staticmethod
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
        Components.bold_text(title)
        Components.easy_tooltip(folder_path)
        imgui.same_line()
        imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() - g.mImguiStyle.frame_padding[1])
        imgui.set_cursor_pos_x(
            imgui.get_cursor_pos_x() + imgui.get_content_region_available_width() - imgui.get_frame_height())
        force_update = Components.icon_button('refresh-line')
        add_mode = False
        if last_add_time is not None:
            if time.time() - last_add_time > 1:
                add_mode = processing_flag
                if last_add_time_callback is not None:
                    last_add_time_callback(time.time())
        thumbnail_info = modules.TextureModule.get_folder_thumbnails(
            folder_path,
            icon_size=int(imgui.get_content_region_available_width() / 4),
            force_update=force_update,
            add_mode=add_mode
        )  # {name : Texture}
        Components.image_gallery(title, thumbnail_info,
                                 width=imgui.get_content_region_available_width(),
                                 height=imgui.get_content_region_available_width() / 2,
                                 columns=4)
        imgui.pop_id()

    _cached_confirm_create_project_path = ''

    @staticmethod
    def create_project_confirm_popup(open_flag, path):
        if open_flag:
            imgui.open_popup('confirm_create_project')
            Components._cached_confirm_create_project_path = path
        if imgui.is_popup_open('confirm_create_project'):
            imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 8)
        if imgui.begin_popup_modal('confirm_create_project', True,
                                   imgui.WINDOW_ALWAYS_AUTO_RESIZE | imgui.WINDOW_NO_TITLE_BAR).opened:
            imgui.text('Cannot find project at: ')
            imgui.push_style_color(imgui.COLOR_TEXT, *modules.StyleModule.COLOR_GRAY)
            imgui.set_window_font_scale(0.8)
            imgui.text(Components._cached_confirm_create_project_path)
            imgui.set_window_font_scale(1.0)
            imgui.pop_style_color()
            imgui.text('Do you want to create project at this location?')
            if imgui.button('YES'):
                ProjectManager.create_project(
                    os.path.basename(Components._cached_confirm_create_project_path), Components._cached_confirm_create_project_path
                )
                imgui.close_current_popup()
            imgui.same_line()
            if imgui.button('NO'):
                imgui.close_current_popup()

            imgui.end_popup()
            imgui.pop_style_var()

    @staticmethod
    def begin_child(name, width=0, height=0, border=True, flags=imgui.WINDOW_NONE):
        imgui.begin_child(name, width, height, border=border, flags=flags)

    _child_height_data: dict[str: float] = {}

    @staticmethod
    def begin_child_auto_height(name, width=0, initial_height=0, border=True, flags=imgui.WINDOW_NO_SCROLLBAR, color=None):
        if name not in Components._child_height_data:
            Components._child_height_data[name] = initial_height
        curr_height = Components._child_height_data[name]

        if color is not None:
            pos = (imgui.get_cursor_pos()[0] + imgui.get_window_position()[0], imgui.get_cursor_pos()[1] + imgui.get_window_position()[1])
            modules.DrawingModule.draw_rect_filled(pos[0], pos[1], pos[0] + 5 * g.global_scale, pos[1] + curr_height,
                                                   col=color, rounding=g.mImguiStyle.child_rounding, draw_list_type="window")

        c.begin_child(name, width, curr_height, border, flags)

    @staticmethod
    def end_child_auto_height(name):
        cursor_pos_y = imgui.get_cursor_pos_y()
        if cursor_pos_y > 20:
            _curr_height = Components._child_height_data[name]
            _target_child_height = cursor_pos_y + g.mImguiStyle.window_padding[1] * 2
            height_delta = _target_child_height - _curr_height
            abs_delta = abs(height_delta)
            delta_in_frame = height_delta * g.mFrametime * 15.0
            delta_in_frame = max(-abs_delta, delta_in_frame)
            delta_in_frame = min(abs_delta, delta_in_frame)
            _curr_height += delta_in_frame
            Components._child_height_data[name] = _curr_height
        # CHILD END ============================================================================
        imgui.end_child()

    @staticmethod
    def quick_menu_item(label, callback=None):
        clicked, state = imgui.menu_item(label)
        if clicked:
            if callback is not None:
                callback()

    @staticmethod
    def get_arg_types(args: dict):
        from gui.utils.arg_utils import ArgType
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

    @staticmethod
    def arg_editor(args: dict, arg_type_dict: dict, disabled_keys: set = None, hidden_keys: set = None,
                   custom_lines: dict[any:Callable] = None, width_percent=0.5):
        width = imgui.get_content_region_available_width() * width_percent
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
                imgui.push_style_color(imgui.COLOR_TEXT, *modules.StyleModule.COLOR_GRAY)
                imgui.set_next_item_width(width)
                imgui.input_text(key, args[key], -1, imgui.INPUT_TEXT_READ_ONLY)
                imgui.pop_style_color()
                continue
            tp: arg_utils.ArgType = arg_type_dict[key]
            if tp == arg_utils.ArgType.INTEGER:
                imgui.set_next_item_width(width)
                changed, args[key] = imgui.input_int(key, args[key])
                any_change |= changed
                continue
            if tp == arg_utils.ArgType.FLOAT:
                imgui.set_next_item_width(width)
                changed, args[key] = imgui.input_float(key, args[key], format='%.5f')
                any_change |= changed
                continue
            if tp == arg_utils.ArgType.BOOLEAN:
                imgui.set_next_item_width(width)
                changed, args[key] = imgui.checkbox(key, args[key])
                any_change |= changed
                continue
            if tp == arg_utils.ArgType.STRING:
                imgui.set_next_item_width(width)
                changed, args[key] = imgui.input_text(key, args[key])
                any_change |= changed
                continue
            if tp == arg_utils.ArgType.PATH:
                changed, args[key] = Components.file_or_folder_selector(key, args[key], width, True)
                any_change |= changed
                continue
            if tp == arg_utils.ArgType.FOLDER:
                changed, args[key] = Components.file_or_folder_selector(key, args[key], width, False)
                any_change |= changed
                continue
            if tp == arg_utils.ArgType.FLOAT2:
                imgui.set_next_item_width(width)
                changed, args[key] = imgui.input_float2(key, *args[key])
                any_change |= changed
                continue
            if tp == arg_utils.ArgType.INT2:
                imgui.set_next_item_width(width)
                changed, args[key] = imgui.input_int2(key, *args[key])
                any_change |= changed
                continue
            if tp == arg_utils.ArgType.OPTIONAL_INT:
                imgui.push_id(key)
                state_key = f'${key}_enabled'
                value_key = f'${key}_value'
                if state_key not in args.keys():
                    # 初始化
                    args[state_key] = args[key] is not None
                if value_key not in args.keys():
                    # 初始化
                    args[value_key] = args[key] if args[key] is not None else 0
                imgui.set_next_item_width(45 * g.global_scale)
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

    @staticmethod
    def file_or_folder_selector(label: str, value: str, width: float, is_file: bool = True) -> tuple[bool, str]:
        any_change = False
        style = g.mImguiStyle
        imgui.set_next_item_width(width - 45 * g.global_scale - style.item_spacing[0])
        imgui.push_id(label)
        changed, value = imgui.input_text('', value)
        any_change |= changed
        imgui.same_line()
        if imgui.button('...', width=45 * g.global_scale):
            if is_file:
                value = io_utils.open_file_dialog()
            else:
                value = io_utils.open_folder_dialog()
            any_change |= True
        imgui.pop_id()
        imgui.same_line()
        imgui.text(label)
        return any_change, value

    _imgui_curr_selected_iteration_folder_idx = -1

    @staticmethod
    def load_gaussian_from_iteration_button(display_text="From Iteration", display_icon="menu-line",
                                            tooltip="Load Gaussian From Project Output", primary_color=True,
                                            uid=None):
        """加载成功返回Gaussian Manager， 未加载或失败返回None"""

        gm = None
        if primary_color:
            modules.StyleModule.push_highlighted_button_color()
        load_file_from_iteration = Components.icon_text_button(
            display_icon, display_text, width=imgui.get_content_region_available_width(), align_center=True, uid=uid)
        if primary_color:
            modules.StyleModule.pop_button_color()
        Components.easy_tooltip(tooltip)
        if load_file_from_iteration:
            imgui.open_popup(f'select_ply_from_iteration_{uid}')

        if imgui.begin_popup(f'select_ply_from_iteration_{uid}'):
            output_point_cloud_folder = ProjectManager.curr_project.info['output_point_cloud_folder']
            output_iteration_folders: list = ProjectManager.curr_project.info['output_iteration_folder_names']
            output_iteration_folder_paths = ProjectManager.curr_project.info['output_iteration_folder_paths']
            if len(output_point_cloud_folder) > 30:
                imgui.text(f'{output_point_cloud_folder[:30]}...')
            else:
                imgui.text(output_point_cloud_folder)
            Components.easy_tooltip(output_point_cloud_folder)
            _, Components._imgui_curr_selected_iteration_folder_idx = imgui.listbox(
                '', Components._imgui_curr_selected_iteration_folder_idx,
                output_iteration_folders)
            modules.StyleModule.push_highlighted_button_color()
            if Components.icon_text_button('checkbox-circle-line', 'Load', width=imgui.get_content_region_available_width() / 2):
                try:
                    from src.manager.gaussian_manager import GaussianManager
                    args = arg_utils.gen_config_args()
                    selected_folder_name = output_iteration_folders[Components._imgui_curr_selected_iteration_folder_idx]
                    selected_folder_path = output_iteration_folder_paths[Components._imgui_curr_selected_iteration_folder_idx]
                    loaded_iteration = int(selected_folder_name.replace('iteration_', ''))
                    ply_path = os.path.join(selected_folder_path, 'point_cloud.ply')
                    args.loaded_iter = loaded_iteration
                    gm = GaussianManager(args, scene_info=None, custom_ply_path=ply_path)

                except Exception as e:
                    logging.error(e)
            modules.StyleModule.pop_button_color()
            imgui.same_line()
            if Components.icon_text_button('refresh-line', 'Refresh Info', width=imgui.get_content_region_available_width()):
                ProjectManager.curr_project.scan_output()
                Components._imgui_curr_selected_iteration_folder_idx = 0
            imgui.end_popup()
        return gm

    @staticmethod
    def load_gaussian_from_custom_file_button(display_text='From Custom File', display_icon='folder-open-line',
                                              tooltip='Load Gaussian From Custom File', uid=None):
        """加载成功返回Gaussian Manager， 未加载或失败返回None"""
        gm = None
        load_file_from_custom_file = Components.icon_text_button(
            display_icon, display_text, width=imgui.get_content_region_available_width() / 2, uid=uid)
        Components.easy_tooltip(tooltip)
        if load_file_from_custom_file:
            ply_path = io_utils.open_file_dialog()
            if ply_path != '' and ply_path is not None:
                try:
                    from src.manager.gaussian_manager import GaussianManager
                    args = arg_utils.gen_config_args()
                    gm = GaussianManager(args, scene_info=None, custom_ply_path=ply_path)
                except Exception as e:
                    logging.error(e)
        return gm

    @staticmethod
    def text_with_max_length(text, max_length):
        max_length = max(max_length, 3)  # 最小支持三位
        if len(text) > max_length:
            display_text = text[:max_length - 3]
            display_text = f"{display_text}..."
            imgui.text(display_text)
            Components.easy_tooltip(text)
        else:
            imgui.text(text)

    @staticmethod
    def move_to_horizontal_right(num_icons):
        imgui.same_line()
        imgui.set_cursor_pos_x(
            imgui.get_cursor_pos_x() + imgui.get_content_region_available_width() - num_icons * (g.mImguiStyle.item_spacing[0] + imgui.get_frame_height())
        )

    @staticmethod
    def move_to_vertical_bottom(num_icons):
        imgui.set_cursor_pos_y(
            imgui.get_cursor_pos_y() + imgui.get_content_region_available()[1] - num_icons * (g.mImguiStyle.item_spacing[1] + imgui.get_frame_height())
        )

    _progress_bar_fbts: dict[str: "ProgressBarFBT"] = {}

    @staticmethod
    def progress_bar(name, width, height, progress, state_value: int = 1):
        """
        values for state, see progress_utils.py for detail
        Prepare = 0
        Running = 1
        Complete = 2
        Error = 3
        NotFound = 4

        :param name:
        :param width:
        :param height:
        :param progress:
        :param state_value:
        :return:
        """
        width = int(width)
        height = int(height)
        if name not in Components._progress_bar_fbts:
            Components._progress_bar_fbts[name] = modules.graphic_module.ProgressBarFBT(width, height)

        _fbt: "ProgressBarFBT" = Components._progress_bar_fbts[name]

        if _fbt.width != width or _fbt.height != height:
            logging.info(f"progress_bar {name} updating size")
            _fbt.update_size(width, height)

        _fbt.render(progress=progress, rounding=g.font_size / 2, state_value=state_value)
        imgui.image(_fbt.texture_id, _fbt.width, _fbt.height)


c = Components()
