import math
import os
import random
import threading
import time
from abc import abstractmethod
from typing import Optional
import moderngl
import numpy as np
import pyperclip
import imgui
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import sys
from io import StringIO

from ImNodeEditor import NE, NEStyle, NEDrawer, NEOP, PinKind
from ImNodeEditor import Node, RightMenuManager

from src.utils import progress_utils as pu
from gui import global_var as g


PIN_TYPES = {'flow', 'any', 'float', 'vector2', 'vector3', 'vector4', 'int', 'str',
             }
PIN_COLORS = {
    'flow': (0.80, 0.80, 0.80, 1.00),
    'float': (0.21, 0.73, 0.27, 1.00),
    'vector2': (0.15, 0.71, 0.41, 1.00),
    'vector3': (0.15, 0.71, 0.67, 1.00),
    'vector4': (0.15, 0.61, 0.71, 1.00),
    'int': (0.00, 0.50, 0.90, 1.00),
    'str': (0.80, 0.00, 0.80, 1.00)
}

NODE_COLORS = {
    'test': (0.22, 0.24, 0.53, 0.40),
    'values': (0.28, 0.51, 0.52, 0.31),
    'converter': (0.18, 0.42, 0.48, 0.50),
    'operation': (0.56, 0.24, 0.51, 0.50),
    'debug': (0.21, 0.25, 0.79, 0.50)
}  # node category colors

FLOW_ICON_OFFSETS = [(-5, -5), (-5, 5), (3, 5), (6.0, 0), (3, -5)]

_tmp_data_storage = {}

db_root = r'D:\M.Arch\MastersThesis\arch-gaussian\shared'


class OutputCapture:
    def __init__(self, target_list):
        self.output_list = target_list
        self.output_text = StringIO()

    def write(self, text):
        self.output_text.write(text)
        if text.endswith('\n'):  # 以换行符判断一次输出结束
            output = self.output_text.getvalue().strip()
            if output != '':
                self.output_list.append(output)
            self.output_text.truncate(0)
            self.output_text.seek(0)

    def __enter__(self):
        self.old_stdout = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.old_stdout


def show_pin_color_editor():
    for key, value in PIN_COLORS.items():
        changed, PIN_COLORS[key] = imgui.color_edit4(key, *value)


def show_node_color_editor():
    for key, value in NODE_COLORS.items():
        changed, NODE_COLORS[key] = imgui.color_edit4(key, *value)


def copy_pin_colors():
    start = "pin_colors = {"
    middle = ",\n              ".join(
        [f"'{key}': ({', '.join(['{:.2f}'.format(i) for i in value])})" for key, value in PIN_COLORS.items()])
    end = "             }"
    code = f"{start}\n              {middle}\n{end}"
    pyperclip.copy(code)


def copy_node_colors():
    start = "node_colors = {"
    middle = ",\n               ".join(
        [f"'{key}': ({', '.join(['{:.2f}'.format(i) for i in value])})" for key, value in NODE_COLORS.items()])
    end = "              }"
    code = f"{start}\n              {middle}\n{end}"
    pyperclip.copy(code)


def get_pin_color(pin_type):
    if pin_type in PIN_COLORS:
        return PIN_COLORS[pin_type]
    return 0.5, 0.5, 0.5, 1


def get_node_color(node_category):
    if node_category in NODE_COLORS:
        return NODE_COLORS[node_category]
    else:
        return 0.8, 0.8, 0.8, 0.5


def pin_icon_factory(pin_uid, pin_kind: PinKind, pin_type: str, enabled: bool):
    pos = NE.mPinPosDict[pin_uid]

    if pin_type == 'flow':
        offset = NEStyle.INIT_STYLE_VAR['frame_padding'][0] + 5
        if pin_kind == PinKind.Output:
            offset *= -1
        pos = NEOP.vec2_add_x(pos, offset)
        pts = [NEOP.vec2_add(pos, offset) for offset in FLOW_ICON_OFFSETS]

        NEDrawer.draw_polyline(pts, get_pin_color(pin_type), 1.0 * NE.mViewScale)
        return 0

    if pin_type != "flow":
        offset = NEStyle.INIT_STYLE_VAR['frame_padding'][0] + 4
        if pin_kind == PinKind.Output:
            offset *= -1
        pos = NEOP.vec2_add_x(pos, offset)
        NEDrawer.draw_circle(*pos, 6, get_pin_color(pin_type), thickness=2 * NE.mViewScale)
        return 0

    return 0


def pin_color_factory(pin_kind: PinKind, pin_type: str, enabled: bool) -> int:
    """

    :param pin_kind:
    :param pin_type:
    :param enabled:
    :return: push的style的个数
    """
    if not enabled:
        imgui.push_style_color(imgui.COLOR_BUTTON, 0, 0, 0, 0.5)
        imgui.push_style_color(imgui.COLOR_TEXT, 0.5, 0.5, 0.5, 0.5)
        return 2
    if pin_type == 'flow':
        imgui.push_style_color(imgui.COLOR_BUTTON, 0.0, 0.0, 0.0, 0.0)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 1.0, 1.0, 1.0, 0.1)
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.0, 0.0, 0.0, 0.0)
        return 3

    c = get_pin_color(pin_type)
    pin_color = (c[0], c[1], c[2], 0.2)
    imgui.push_style_color(imgui.COLOR_BUTTON, 0.5, 0.5, 0.5, 0.1)
    imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *pin_color)
    imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.0, 0.0, 0.0, 0.0)
    return 3


NE.set_pin_color_factory(pin_color_factory)
NE.set_pin_icon_factory(pin_icon_factory)


def create_texture_from_image(image: Image) -> moderngl.Texture:
    # must be called after NE.set_window_event()
    width, height = image.size
    channels = 3 if image.mode == 'RGB' else 4
    data = image.tobytes()
    texture = NE.WINDOW_EVENT.ctx.texture((width, height), channels, data)
    NE.WINDOW_EVENT.imgui.register_texture(texture)
    return texture


def update_texture(texture_id, image: Image):
    assert texture_id in NE.WINDOW_EVENT.imgui._textures.keys()
    texture: moderngl.Texture = NE.WINDOW_EVENT.imgui._textures[texture_id]
    texture.write(image.tobytes())


def remove_texture(texture_id):
    assert texture_id in NE.WINDOW_EVENT.imgui._textures.keys()
    NE.WINDOW_EVENT.imgui.remove_texture(NE.WINDOW_EVENT.imgui._textures[texture_id])


def right_menu_item(name, category):
    """right menu decorator"""

    def decorator(cls):
        RightMenuManager.register_node_class(cls, name, category)
        cls.category = category
        return cls

    return decorator


bg_img = Image.open(os.path.join(g.GUI_RESOURCES_ROOT, 'BlueprintBackground.png'))

bg_texture_dict = {}


class NodeSimpleTemplate(Node):
    """拥有常规输入输出以及参数的节点， 实现了Node的draw函数"""
    category = ''

    def __init__(self, name, width,
                 input_names=None, input_types=None,
                 output_names=None, output_types=None):
        # custom content 需要返回是否发生改变的布尔值
        super().__init__()
        if output_types is None:
            output_types = []
        if input_types is None:
            input_types = []
        if input_names is None:
            input_names = []
        if output_names is None:
            output_names = []
        self.width = width
        self.name = name

        # pin and ids
        self.input_ids = [Node.get_unique_id() for _ in input_names]
        self.output_ids = [Node.get_unique_id() for _ in output_names]
        # 如果需要动态扩充输入输出pin的数量， 需要同时更新names， types 和ids

        # init inputs and outputs
        self.input_names = input_names
        self.output_names = output_names
        self.input_types = input_types
        self.output_types = output_types

        for uid in self.input_ids:
            self.input[uid] = None
        for uid in self.output_ids:
            self.output[uid] = None

    def _init_bg_texture(self):
        if self.name not in bg_texture_dict:
            bg_ratio = max(self.width / 64.0, 1.0)

            img_width = bg_img.width
            img_height = int(img_width / bg_ratio)

            start_y = random.randint(0, bg_img.height - img_height)
            cropped_image = bg_img.crop((0, start_y, img_width, start_y + img_height))
            img_arr = np.array(cropped_image)

            alpha_array = np.linspace(1.0, -0.5, num=img_height).clip(0, 1)
            alpha_grid = np.tile(alpha_array, (img_width, 1)).T
            img_arr[:, :, 3] = (img_arr[:, :, 3] * alpha_grid).astype(np.uint8)
            processed_image = Image.fromarray(img_arr)
            bg_texture_dict[self.name] = create_texture_from_image(processed_image)

    def _draw_input_pins(self):
        imgui.begin_group()
        for i in range(len(self.input_names)):
            NE.pin(self.input_ids[i], self.input_names[i], PinKind.Input, self.input_types[i])
            if imgui.is_item_hovered():
                imgui.set_tooltip(
                    f'name: {self.input_names[i]}\ntype: {self.input_types[i]}\nvalue: {self.input[self.input_ids[i]]}')
        imgui.end_group()

    def _draw_output_pins(self):
        imgui.begin_group()
        for i in range(len(self.output_names)):
            NE.pin(self.output_ids[i], self.output_names[i], PinKind.Output, self.output_types[i])
            if imgui.is_item_hovered():
                imgui.set_tooltip(
                    f'name: {self.output_names[i]}\ntype: {self.output_types[i]}\nvalue: {self.output[self.output_ids[i]]}')
        imgui.end_group()

    def _draw_node_status(self):
        if self.error:
            color = (1, 0, 0, 0.5)
        elif not self.valid:
            color = (1, 1, 0, 0.5)
        elif self.cached:
            color = (0, 1, 0, 0.5)
        else:
            return
        org_pos = imgui.get_cursor_pos()
        button_size = 12
        x = imgui.get_window_width() - imgui.get_cursor_pos_x() - button_size * NE.mViewScale
        imgui.set_cursor_pos_x(x)
        imgui.push_style_var(imgui.STYLE_FRAME_ROUNDING, button_size / 2 * NE.mViewScale)
        imgui.push_style_color(imgui.COLOR_BUTTON, *color)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *color)
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, *color)
        imgui.push_id('info button')
        button_clicked = imgui.button('', button_size * NE.mViewScale, button_size * NE.mViewScale)
        imgui.pop_id()
        imgui.pop_style_var()
        imgui.pop_style_color(3)
        imgui.set_cursor_pos(org_pos)
        if imgui.is_item_hovered():
            imgui.begin_tooltip()
            if self.error:
                imgui.push_style_color(imgui.COLOR_TEXT, 1, 0, 0, 1)
                imgui.text(self.error_msg)
                imgui.pop_style_color()
            if not self.valid:
                imgui.push_style_color(imgui.COLOR_TEXT, 1, 1, 0, 1)
                imgui.text('not valid')
                imgui.pop_style_color()
            if self.cached:
                imgui.push_style_color(imgui.COLOR_TEXT, 0.2, 0.8, 0.2, 1)
                imgui.text('output cached')
                imgui.pop_style_color()
                imgui.text('click to clear cache')
            imgui.end_tooltip()
        if button_clicked:
            if self.cached:
                self.cached = False
            else:
                imgui.open_popup('node status')
        if imgui.begin_popup('node status'):
            if self.error:
                imgui.push_style_color(imgui.COLOR_TEXT, 1, 0, 0, 1)
                imgui.text(self.error_msg)
                imgui.pop_style_color()
            if not self.valid:
                imgui.push_style_color(imgui.COLOR_TEXT, 1, 1, 0, 1)
                imgui.text('not valid')
                imgui.pop_style_color()
            imgui.end_popup()
        # x, y = NEOP.world2window(x, y)
        # radius = 2 * NE.mViewScale
        # imgui.get_window_draw_list().add_circle_filled(x, y, radius, imgui.get_color_u32_rgba(*color))

    def _draw_node_header(self):
        style: imgui.core.GuiStyle = imgui.get_style()
        rounding = style.child_rounding
        border_size = style.child_border_size
        world_x, world_y = NE.mNodePosX[self.uid], NE.mNodePosY[self.uid]
        world_size_x, world_size_y = NE.mNodeWidth[self.uid], 40
        min_x, min_y = NEOP.world2window(world_x, world_y)
        max_x, max_y = NEOP.world2window((world_x + world_size_x), (world_y + world_size_y))
        min_x += border_size
        max_x -= border_size
        uv0 = (0, 0)
        uv1 = (1, 0.66)
        if self.name not in bg_texture_dict:
            self._init_bg_texture()
        texture_id = bg_texture_dict[self.name].glo
        color = get_node_color(self.__class__.category)
        imgui.get_foreground_draw_list().add_image_rounded(
            texture_id, (min_x, min_y), (max_x, max_y), uv0, uv1, col=imgui.get_color_u32_rgba(*color),
            rounding=rounding)

    def draw(self):
        NE.begin_node(self.uid, self.name, self.init_x, self.init_y, self.width)
        self._draw_node_header()
        self._draw_node_status()

        with imgui.font(g.mNodeEditorFontBold):
            imgui.text(self.name)
        imgui.push_id(str(self.uid))
        if self.input_names:
            self._draw_input_pins()
            # 如果有input，则output前置， 参数后置
            if self.output_names:
                imgui.same_line()
                self._draw_output_pins()

        imgui.begin_group()
        any_change = self.draw_parameters()
        imgui.end_group()
        if any_change:
            self.cached = False

        if not self.input_names and self.output_names:
            # 如果没有input，则output后置
            imgui.same_line()
            self._draw_output_pins()
        imgui.pop_id()
        NE.end_node()

    @abstractmethod
    def draw_parameters(self) -> bool:
        """返回是否有参数变化"""
        return False

    @abstractmethod
    def process(self):
        pass


@right_menu_item('NodeTest', 'test')
class NodeTest(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='NodeTest', width=200,
                         input_names=['', 'in1', 'in2', 'in3', ],
                         input_types=['flow', 'int', 'float', 'str'],
                         output_names=['out1'],
                         output_types=['any'])
        self._value1 = 0.1
        self._value2 = 0.2

    def draw_parameters(self):
        any_change = False
        imgui.push_id('input1')
        imgui.set_next_item_width(100 * NE.mViewScale)
        changed, self._value1 = imgui.input_int('some parameter', self._value1)
        any_change |= changed
        imgui.pop_id()
        imgui.push_id('input2')
        changed, self._value2 = imgui.input_float('input2', self._value2)
        any_change |= changed
        imgui.pop_id()
        return any_change

    def process(self):
        pass


@right_menu_item('Time Consumer', 'test')
class NodeTimeConsumer(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Time Consumer', width=200,
                         input_names=['input'],
                         input_types=['any'],
                         output_names=['output'],
                         output_types=['any'])
        self.display_text = ''
        self.progress = 0.0
        self.expanded = False
        self.log_msgs = []

    def draw_parameters(self):
        imgui.push_style_color(imgui.COLOR_PLOT_HISTOGRAM, 0.00, 0.45, 0.77, 1.00)
        imgui.progress_bar(self.progress, (imgui.get_content_region_available_width(), 10 * NE.mViewScale))
        imgui.pop_style_color()
        imgui.text_wrapped(f'status: {self.display_text}')
        if imgui.button('expand', width=imgui.get_content_region_available_width()):
            self.expanded = not self.expanded
        if self.expanded:
            imgui.begin_child(f'{self.uid} log msgs', 0, 200 * NE.mViewScale, border=True)
            imgui.set_window_font_scale(NE.mViewScale)
            NE.forbidden_zoom_when_window_hovered()
            for msg in self.log_msgs:
                imgui.text(msg)
            imgui.end_child()

        return False

    def process(self):
        total = 100
        self.progress = 0.0
        self.log_msgs = []
        for i in range(total):
            self.display_text = f'running...{i}%'
            self.progress = (i + 1.0) / total
            self.log_msgs.append(f'some msg {i}')
            time.sleep(0.02)

            if Node.event.is_set():
                self.display_text = 'break'
                raise Exception('用户取消')
        self.output[self.output_ids[0]] = self.input[self.input_ids[0]]
        self.display_text = 'complete'


@right_menu_item('Float', 'values')
class NodeFloat(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Float', width=160,
                         output_names=['value'],
                         output_types=['float'])
        self._param_value = 0.0

    def draw_parameters(self):
        imgui.set_next_item_width(80 * NE.mViewScale)
        changed, self._param_value = imgui.input_float('', self._param_value)
        return changed

    def process(self):
        self.output[self.output_ids[0]] = self._param_value


@right_menu_item('Vector2', 'values')
class NodeVector2(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Vector2', width=180,
                         output_names=['value'],
                         output_types=['vector2'])
        self._param_value = (0, 0)

    def draw_parameters(self):
        imgui.set_next_item_width(100 * NE.mViewScale)
        changed, self._param_value = imgui.input_float2('', *self._param_value)
        return changed

    def process(self):
        self.output[self.output_ids[0]] = self._param_value


@right_menu_item('Vector3', 'values')
class NodeVector3(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Vector3', width=200,
                         output_names=['value'],
                         output_types=['vector3'])
        self._param_value = (0, 0, 0)

    def draw_parameters(self):
        imgui.set_next_item_width(120 * NE.mViewScale)
        changed, self._param_value = imgui.input_float3('', *self._param_value)
        return changed

    def process(self):
        self.output[self.output_ids[0]] = self._param_value


@right_menu_item('Vector4', 'values')
class NodeVector4(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Vector4', width=220,
                         output_names=['value'],
                         output_types=['vector4'])
        self._param_value = (0, 0, 0, 0)

    def draw_parameters(self):
        imgui.set_next_item_width(140 * NE.mViewScale)
        changed, self._param_value = imgui.input_float4('', *self._param_value)
        return changed

    def process(self):
        self.output[self.output_ids[0]] = self._param_value


@right_menu_item('Int', 'values')
class NodeInt(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Int', width=160,
                         output_names=['value'],
                         output_types=['int'])
        self._param_value = 0

    def draw_parameters(self):
        imgui.set_next_item_width(80 * NE.mViewScale)
        changed, self._param_value = imgui.input_int('', self._param_value)
        return changed

    def process(self):
        self.output[self.output_ids[0]] = self._param_value


@right_menu_item('String', 'values')
class NodeString(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='String', width=160,
                         output_names=['value'],
                         output_types=['str'])
        self._param_value = ''

    def draw_parameters(self):
        imgui.set_next_item_width(80 * NE.mViewScale)
        changed, self._param_value = imgui.input_text('', self._param_value)
        return changed

    def process(self):
        self.output[self.output_ids[0]] = self._param_value


@right_menu_item('File Browser', 'values')
class NodeFileBrowser(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='File Browser', width=160,
                         output_names=['path'],
                         output_types=['str'])
        self._param_value = ''

    def draw_parameters(self):
        any_change = False
        if imgui.button("Open File"):
            root = tk.Tk()
            root.withdraw()
            # 打开文件选择窗口
            file_path = filedialog.askopenfilename()
            # 手动关闭根窗口
            root.destroy()
            # 显示选择的文件路径
            if file_path:
                print("Selected file:", file_path)
                self._param_value = file_path
                any_change = True
        imgui.text(self._param_value)
        if imgui.is_item_hovered():
            imgui.set_tooltip(self._param_value)
        return any_change

    def process(self):
        self.output[self.output_ids[0]] = self._param_value


@right_menu_item('Folder Browser', 'values')
class NodeFolderBrowser(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Folder Browser', width=160,
                         output_names=['path'],
                         output_types=['str'])
        self._param_value = ''

    def draw_parameters(self):
        any_change = False
        if imgui.button("Open Folder"):
            root = tk.Tk()
            root.withdraw()
            # 打开文件选择窗口
            folder_path = filedialog.askdirectory()
            # 手动关闭根窗口
            root.destroy()
            # 显示选择的文件路径
            if folder_path:
                print("Selected file:", folder_path)
                self._param_value = folder_path
                any_change = True
        imgui.text(self._param_value)
        if imgui.is_item_hovered():
            imgui.set_tooltip(self._param_value)
        return any_change

    def process(self):
        self.output[self.output_ids[0]] = self._param_value


@right_menu_item('Input Scene Browser', 'values')
class NodeInputSceneBrowser(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Input Scene Browser', width=160,
                         input_names=['db root'],
                         input_types=['str'],
                         output_names=['scene folder'],
                         output_types=['str'])
        self.width = 300

        self.curr_folder = os.path.join(db_root, 'data')
        self.target_folder = self.curr_folder
        self.curr_sub_folder_names = []
        self.curr_sub_folder_selected = []
        self.update_curr_sub_folders()
        self.curr_folder_idx = -1

    def get_sub_folders(self, folder):
        subdirectories = []
        for entry in os.scandir(folder):
            if entry.is_dir():
                subdirectories.append(entry.name)
        return subdirectories

    def update_curr_sub_folders(self):
        if self.curr_folder is None:
            self.curr_sub_folder_names = []
            return
        subdirectories = ['..']
        for entry in os.scandir(self.curr_folder):
            if entry.is_dir():
                subdirectories.append(entry.name)
        self.curr_sub_folder_names = subdirectories
        self.curr_sub_folder_selected = [False] * len(self.curr_sub_folder_names)

    def draw_parameters(self):
        any_change = False
        imgui.begin_child('folders', imgui.get_content_region_available_width(), 100 * NE.mViewScale, border=True)
        imgui.set_window_font_scale(NE.mViewScale)
        NE.forbidden_zoom_when_window_hovered()
        for i, folder_name in enumerate(self.curr_sub_folder_names):
            clicked, state = imgui.menu_item(folder_name, None, self.curr_sub_folder_selected[i])
            if clicked:
                if folder_name == '..':
                    self.curr_folder = os.path.dirname(self.curr_folder)
                    self.target_folder = self.curr_folder
                    self.update_curr_sub_folders()
                    any_change |= True
                else:
                    # first check subfolders
                    sub_folders = self.get_sub_folders(os.path.join(self.curr_folder, folder_name))
                    if 'input' in sub_folders or 'distorted' in sub_folders:
                        self.target_folder = os.path.join(self.curr_folder, folder_name)
                        self.curr_sub_folder_selected = [False] * len(self.curr_sub_folder_selected)
                        self.curr_sub_folder_selected[i] = True
                        any_change |= True
                    else:
                        print('select')
                        any_change |= True
                        self.curr_folder = os.path.join(self.curr_folder, folder_name)
                        self.target_folder = self.curr_folder
                        self.update_curr_sub_folders()

        imgui.end_child()
        # changed, self.curr_folder_idx = imgui.listbox('folders', self.curr_folder_idx, self.curr_sub_folder_names)
        # any_change |= changed
        # if changed:
        #     print('select')
        #     curr_selected_folder_name = self.curr_sub_folder_names[self.curr_folder_idx]
        #     print(curr_selected_folder_name)
        #     if curr_selected_folder_name == '..':
        #         self.curr_folder = os.path.dirname(self.curr_folder)
        #     else:
        #         self.curr_folder = os.path.join(self.curr_folder, curr_selected_folder_name)
        #     self.update_curr_sub_folders()
        #     self.curr_folder_idx = -1
        imgui.text_wrapped(self.target_folder)
        return any_change

    def process(self):
        self.output[self.output_ids[0]] = None


@right_menu_item('Int To Float', 'converter')
class NodeIntToFloat(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Int To Float', width=200,
                         input_names=['value'],
                         input_types=['int'],
                         output_names=['value'],
                         output_types=['float'])

    def draw_parameters(self):
        return False

    def process(self):
        self.output[self.output_ids[0]] = float(self.input[self.input_ids[0]])


@right_menu_item('Float To Int', 'converter')
class NodeFloatToInt(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Float To Int', width=200,
                         input_names=['value'],
                         input_types=['float'],
                         output_names=['value'],
                         output_types=['int'])

    def draw_parameters(self):
        return False

    def process(self):
        self.output[self.output_ids[0]] = int(self.input[self.input_ids[0]])


@right_menu_item('Construct Vector', 'converter')
class NodeConstructVector(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Construct Vector', width=200,
                         input_names=['x', 'y'],
                         input_types=['float'] * 2,
                         output_names=['vector2'],
                         output_types=['vector2'])
        self.selections = ['vector2', 'vector3', 'vector4']
        self.curr_selection = 0
        self.input_ids += [Node.get_unique_id() for _ in range(2)]

    def draw_parameters(self):
        imgui.set_next_item_width(100 * NE.mViewScale)
        changed, new_selection = imgui.combo('output type', self.curr_selection, self.selections)
        if changed:
            new_type = self.selections[new_selection]
            if self.output_ids[0] in NE.mSrcToDsts:
                dsts = NE.mSrcToDsts[self.output_ids[0]]
                for dst in dsts:
                    if NE.mPinTypeDict[dst] != new_type:
                        return False
            if new_selection == 0:
                if self.input_ids[2] in NE.mDstToSrc or self.input_ids[3] in NE.mDstToSrc:
                    return False
                self.curr_selection = new_selection
                self.input_names = ['x', 'y']
                self.input_types = ['float'] * 2
                self.output_names = ['vector2']
                self.output_types = ['vector2']
            elif new_selection == 1:
                if self.input_ids[3] in NE.mDstToSrc:
                    return False
                self.curr_selection = new_selection
                self.input_names = ['x', 'y', 'z']
                self.input_types = ['float'] * 3
                self.output_names = ['vector3']
                self.output_types = ['vector3']
            elif new_selection == 2:
                self.curr_selection = new_selection
                self.input_names = ['x', 'y', 'z', 'w']
                self.input_types = ['float'] * 4
                self.output_names = ['vector4']
                self.output_types = ['vector4']
        return changed

    def process(self):
        result = []
        for i in range(len(self.input_names)):
            result.append(self.input[self.input_ids[i]])
        self.output[self.output_ids[0]] = tuple(result)


@right_menu_item('Deconstruct Vector', 'converter')
class NodeDeconstructVector(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Deconstruct Vector', width=200,
                         input_names=['vector2'],
                         input_types=['vector2'],
                         output_names=['x', 'y'],
                         output_types=['float'] * 2)
        self.selections = ['vector2', 'vector3', 'vector4']
        self.curr_selection = 0
        self.output_ids += [Node.get_unique_id() for _ in range(2)]

    def draw_parameters(self):
        imgui.set_next_item_width(100 * NE.mViewScale)
        changed, new_selection = imgui.combo('input type', self.curr_selection, self.selections)
        if changed:
            new_type = self.selections[new_selection]
            if self.input_ids[0] in NE.mDstToSrc and NE.mPinTypeDict[NE.mDstToSrc[self.input_ids[0]]] != new_type:
                return False
            if new_selection == 0:
                if self.output_ids[2] in NE.mSrcToDsts or self.output_ids[3] in NE.mSrcToDsts:
                    return False
                self.curr_selection = new_selection
                self.output_names = ['x', 'y']
                self.output_types = ['float'] * 2
                self.input_names = ['vector2']
                self.input_types = ['vector2']
            elif new_selection == 1:
                if self.output_ids[3] in NE.mSrcToDsts:
                    return False
                self.curr_selection = new_selection
                self.output_names = ['x', 'y', 'z']
                self.output_types = ['float'] * 3
                self.input_names = ['vector3']
                self.input_types = ['vector3']
            elif new_selection == 2:
                self.curr_selection = new_selection
                self.output_names = ['x', 'y', 'z', 'w']
                self.output_types = ['float'] * 4
                self.input_names = ['vector4']
                self.input_types = ['vector4']
        return changed

    def process(self):
        output_values = list(self.input[self.input_ids[0]])
        for i in range(len(self.output_names)):
            self.output[self.output_ids[i]] = output_values[i]


@right_menu_item('Float Operation', 'operation')
class NodeFloatAdd(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Float Operation', width=200,
                         input_names=['value1', 'value2'],
                         input_types=['float', 'float'],
                         output_names=['value'],
                         output_types=['float'])

        self.op_mode = 0
        self.op_modes = ['Add', 'Sub', 'Mul', 'Divide', 'Pow']

    def draw_parameters(self):
        imgui.set_next_item_width(100 * NE.mViewScale)
        changed, self.op_mode = imgui.combo('Mode', self.op_mode, self.op_modes)
        return changed

    def process(self):
        input1 = self.input[self.input_ids[0]]
        input2 = self.input[self.input_ids[1]]
        if self.op_mode == 0:
            output = input1 + input2
        elif self.op_mode == 1:
            output = input1 - input2
        elif self.op_mode == 2:
            output = input1 * input2
        elif self.op_mode == 3:
            output = input1 / input2
        elif self.op_mode == 4:
            output = math.pow(input1, input2)
        else:
            self.error = True
            output = None
        self.output[self.output_ids[0]] = output


@right_menu_item('Debug', 'debug')
class NodeDebug(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Debug', width=200,
                         input_names=['input'],
                         input_types=['any'])
        self.display_text = ''
        self.is_async = True
        self.thread = None
        self.manually_stop = False

    def draw_parameters(self):
        any_change = False
        changed, state = imgui.checkbox('async', self.is_async)
        if changed:
            any_change |= True
            self.is_async = state

        if self.thread is not None:
            # 存在线程， 说明还未运行到process函数， 存在两种情况，线程正在正常运行和线程已经停止了
            if not self.thread.is_alive():
                # 如果线程已经停止， 又存在两种情况， 分别为 线程在之前遇到了问题 和 手动停止的
                if self.manually_stop:
                    # 如果是手动设置的停止线程
                    self.thread = None
                    self.manually_stop = False
                    self.display_text = '已停止'
                else:
                    # 如果是遇到问题而停止的
                    self.thread = None
                    self.display_text = '运算线程在到达本节点前以外停止了， 请检查'
            else:
                # 线程正在运行
                if self.manually_stop:
                    # 如果已经设置了手动停止线程， 正在等待线程结束
                    imgui.text('正在等待线程结束')
                else:
                    # 线程正在正常运行中
                    if imgui.button('stop', imgui.get_content_region_available_width(), 30 * NE.mViewScale):
                        Node.event.set()
                        self.manually_stop = True

        else:
            # 不存在线程
            if imgui.button('run', imgui.get_content_region_available_width(), 30 * NE.mViewScale):
                self.get_prev_nodes()  # 检查节点连接是否正确
                if self.valid:
                    if self.is_async:
                        self.cached = False  # 强制运行process函数，否则按照缓存机制将会跳过process
                        Node.event.clear()  # 清理event
                        self.display_text = 'waiting...'
                        self.thread = threading.Thread(target=self.run)
                        self.thread.start()
                    else:
                        self.run()
                else:
                    self.display_text = '请检查自身连接'

        imgui.text_wrapped(f'output: {self.display_text}')
        return False

    def process(self):
        self.thread = None
        self.display_text = str(self.input[self.input_ids[0]])


@right_menu_item('Start Flow', 'debug')
class NodeStartFlow(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Start Flow', width=100,
                         output_names=['flow'],
                         output_types=['flow'])

    def draw_parameters(self):
        return False

    def process(self):
        pass


@right_menu_item('End Flow', 'debug')
class NodeEndFlow(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='End Flow', width=200,
                         input_names=['flow'],
                         input_types=['flow'])
        self.display_text = ''
        self.is_async = True
        self.thread = None
        self.manually_stop = False

    def draw_parameters(self):
        any_change = False
        # changed, state = imgui.checkbox('async', self.is_async)
        # if changed:
        #     any_change |= True
        #     self.is_async = state

        if self.thread is not None:
            # 存在线程， 说明还未运行到process函数， 存在两种情况，线程正在正常运行和线程已经停止了
            if not self.thread.is_alive():
                # 如果线程已经停止， 又存在两种情况， 分别为 线程在之前遇到了问题 和 手动停止的
                if self.manually_stop:
                    # 如果是手动设置的停止线程
                    self.thread = None
                    self.manually_stop = False
                    self.display_text = '已停止'
                else:
                    # 如果是遇到问题而停止的
                    self.thread = None
                    self.display_text = '运算线程在到达本节点前以外停止了， 请检查'
            else:
                # 线程正在运行
                if self.manually_stop:
                    # 如果已经设置了手动停止线程， 正在等待线程结束
                    imgui.text('正在等待线程结束')
                else:
                    # 线程正在正常运行中
                    if imgui.button('stop', imgui.get_content_region_available_width(), 30 * NE.mViewScale):
                        Node.event.set()
                        self.manually_stop = True

        else:
            # 不存在线程
            if imgui.button('run', imgui.get_content_region_available_width(), 30 * NE.mViewScale):
                self.get_prev_nodes()  # 检查节点连接是否正确
                if self.valid:
                    if self.is_async:
                        self.cached = False  # 强制运行process函数，否则按照缓存机制将会跳过process
                        Node.event.clear()  # 清理event
                        self.display_text = 'waiting...'
                        self.thread = threading.Thread(target=self.run)
                        self.thread.start()
                    else:
                        self.run()
                else:
                    self.display_text = '请检查自身连接'

        # imgui.text_wrapped(f'output: {self.display_text}')
        return any_change

    def process(self):
        self.thread = None
        self.display_text = str(self.input[self.input_ids[0]])


@right_menu_item('Image Viewer', 'debug')
class NodeImageViewer(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Image Viewer', width=200,
                         input_names=['file path'],
                         input_types=['str'])
        self.texture: Optional[moderngl.Texture] = None

    def draw_parameters(self):
        if imgui.button('update', (self.width - 20) * NE.mViewScale, 30 * NE.mViewScale):
            self.run()
        imgui.text(f'image: ')

        if self.texture is not None:
            img_width = imgui.get_content_region_available_width()
            img_height = img_width * self.texture.height / self.texture.width
            imgui.image(self.texture.glo, img_width, img_height)
        else:
            imgui.text('No Image')
        return False

    def on_save(self):
        super().on_save()
        _tmp_data_storage[f'{self.uid}_texture'] = self.texture
        self.texture = None

    def on_save_complete(self):
        super().on_save_complete()
        key = f'{self.uid}_texture'
        self.texture = _tmp_data_storage[key]
        _tmp_data_storage.pop(key)

    def process(self):
        img_path = self.input[self.input_ids[0]]
        img = Image.open(img_path)
        width, height = img.size
        depth = 3 if img.mode == 'RGB' else 4
        if self.texture is not None and (
                height != self.texture.height or width != self.texture.width or depth != self.texture.depth):
            remove_texture(self.texture.glo)
            self.texture = None
        if self.texture is None:
            self.texture = create_texture_from_image(img)
        else:
            update_texture(self.texture.glo, img)


@right_menu_item('Extract Frames', 'prepare tools')
class NodeExtractFrames(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Extract Frames', width=200,
                         input_names=['video path'],
                         input_types=['str'],
                         output_names=['output folder'],
                         output_types=['str'])
        self.width = 240
        self.curr_frame = 0
        self.target_frames = 30
        self.indent_frames = 0

    def draw_parameters(self):
        any_change = False
        imgui.set_next_item_width(80 * NE.mViewScale)
        changed, self.target_frames = imgui.input_int('target frames', self.target_frames, 10)
        any_change |= changed
        imgui.set_next_item_width(80 * NE.mViewScale)
        changed, self.indent_frames = imgui.input_int('indent frames', self.indent_frames, 10)
        any_change |= changed
        imgui.progress_bar(self.curr_frame / self.target_frames,
                           (imgui.get_content_region_available_width(), 10 * NE.mViewScale))
        imgui.text(f'progress: {self.curr_frame}/{self.target_frames}')
        if self.output[self.output_ids[0]]:
            if imgui.button('open output folder'):
                os.startfile(self.output[self.output_ids[0]])
        return False

    def update_progress(self, value):
        self.curr_frame = value

    def process(self):
        from src.utils.video_utils import extract_frames
        pu.create_contex('extract_frames', self.update_progress, )
        success, output_folder = extract_frames(
            self.input[self.input_ids[0]],
            target_frames=self.target_frames,
            indent_frames=self.indent_frames)
        self.output[self.output_ids[0]] = output_folder


@right_menu_item('Colmap Args', 'prepare tools')
class NodeColmapArgs(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Colmap Args', width=200,
                         input_names=['source path'],
                         input_types=['str'],
                         output_names=['colmap args'],
                         output_types=['any'])
        self.width = 240

    def draw_parameters(self):
        return False

    def process(self):
        from argparse import Namespace
        source_path = self.input[self.input_ids[0]]
        colmap_executable = r'C:\Program Files\COLMAP-3.9.1-windows-cuda\COLMAP.bat'
        colmap_args = Namespace(
            no_gpu=False,
            skip_matching=False,
            source_path=source_path,
            camera="OPENCV",
            colmap_executable=colmap_executable,
            resize=False,
            magick_executable=""
        )
        self.output[self.output_ids[0]] = colmap_args


@right_menu_item('Colmap Matching', 'prepare tools')
class NodeColmapMatching(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Colmap Matching', width=200,
                         input_names=['flow', 'colmap args'],
                         input_types=['flow', 'any'],
                         output_names=['flow'],
                         output_types=['flow'])
        self.width = 240
        self.status = 'idle'
        self.output_msgs = []

    def draw_parameters(self):
        imgui.text(f'status: {self.status}')
        if self.output_msgs:
            imgui.set_next_item_width(imgui.get_content_region_available_width())
            imgui.push_style_color(imgui.COLOR_TEXT, 0.5, 0.5, 0.5, 1)
            imgui.text_wrapped(self.output_msgs[-1])
            imgui.pop_style_color()
            if imgui.button('view logs'):
                imgui.open_popup('NodeColmapMatchingLogsPopup')
            if imgui.begin_popup('NodeColmapMatchingLogsPopup'):
                imgui.begin_child('NodeColmapMatchingLogsChild', 600, 600, border=True)
                NE.forbidden_zoom_when_window_hovered()
                for i in range(len(self.output_msgs)):
                    imgui.text_wrapped(self.output_msgs[len(self.output_msgs) - i - 1])
                imgui.end_child()
                imgui.end_popup()

    def process(self):
        from src.utils.system_utils import run_colmap_feature_extraction, run_colmap_matching_block, \
            run_colmap_bundle
        args = self.input[self.input_ids[1]]
        self.status = 'running'
        self.output_msgs = []
        with OutputCapture(self.output_msgs):
            len_files = len(os.listdir(os.path.join(args.source_path, "input")))
            print(f"共有{len_files}个文件")
            colmap_command = '"{}"'.format(args.colmap_executable) if len(args.colmap_executable) > 0 else "colmap"
            print(colmap_command)
            magick_command = '"{}"'.format(args.magick_executable) if len(args.magick_executable) > 0 else "magick"
            print(magick_command)
            use_gpu = 1 if not args.no_gpu else 0
            # matching
            if args.skip_matching:
                print(f'skip matching')
                self.output[self.output_ids[0]] = args
                return
            os.makedirs(args.source_path + "/distorted/sparse", exist_ok=True)
            # feature extraction
            feat_extracton_cmd = colmap_command + " feature_extractor " \
                                                  "--database_path " + args.source_path + "/distorted/database.db \
                    --image_path " + args.source_path + "/input \
                    --ImageReader.single_camera 1 \
                    --ImageReader.camera_model " + args.camera + " \
                    --SiftExtraction.use_gpu " + str(use_gpu)
            print("start feat extraction cmd")
            print(feat_extracton_cmd)
            run_colmap_feature_extraction(feat_extracton_cmd)
            # feature matching
            feat_matching_cmd = colmap_command + " exhaustive_matcher \
                        --database_path " + args.source_path + "/distorted/database.db \
                        --SiftMatching.use_gpu " + str(use_gpu)
            exit_code = run_colmap_matching_block(feat_matching_cmd)
            if exit_code:
                self.status = 'error'
                raise Exception(f"Feature matching failed with code {exit_code}.")

            # Bundle adjustment
            # The default Mapper tolerance is unnecessarily large,
            # decreasing it speeds up bundle adjustment steps.
            mapper_cmd = (colmap_command + " mapper \
                    --database_path " + args.source_path + "/distorted/database.db \
                    --image_path " + args.source_path + "/input \
                    --output_path " + args.source_path + "/distorted/sparse \
                    --Mapper.ba_global_function_tolerance=0.000001")
            exit_code = run_colmap_bundle(mapper_cmd, len_files)
            if exit_code:
                self.status = 'error'
                raise Exception(f"Mapper failed with code {exit_code}.")
            print("done.")
        self.status = 'done'


@right_menu_item('Colmap Image UnDistortion', 'prepare tools')
class NodeColmapImageUnDistortion(NodeSimpleTemplate):
    def __init__(self):
        super().__init__(name='Colmap Image UnDistortion', width=200,
                         input_names=['flow', 'colmap args'],
                         input_types=['flow', 'any'],
                         output_names=['flow'],
                         output_types=['flow'])
        self.width = 240
        self.status = 'idle'
        self.output_msgs = []

    def draw_parameters(self):
        imgui.text(f'status: {self.status}')
        if self.output_msgs:
            imgui.set_next_item_width(imgui.get_content_region_available_width())
            imgui.push_style_color(imgui.COLOR_TEXT, 0.5, 0.5, 0.5, 1)
            imgui.text_wrapped(self.output_msgs[-1])
            imgui.pop_style_color()
            if imgui.button('view logs'):
                imgui.open_popup('NodeColmapImageUnDistortionLogsPopup')
            if imgui.begin_popup('NodeColmapImageUnDistortionLogsPopup'):
                imgui.begin_child('NodeColmapImageUnDistortionLogsChild', 600, 600, border=True)
                NE.forbidden_zoom_when_window_hovered()
                for i in range(len(self.output_msgs)):
                    imgui.text_wrapped(self.output_msgs[len(self.output_msgs) - i - 1])
                imgui.end_child()
                imgui.end_popup()
        return False

    def process(self):
        from src.utils.system_utils import run_command
        import shutil
        args = self.input[self.input_ids[1]]
        self.status = 'running'
        self.output_msgs = []
        with OutputCapture(self.output_msgs):
            colmap_command = '"{}"'.format(args.colmap_executable) if len(args.colmap_executable) > 0 else "colmap"
            magick_command = '"{}"'.format(args.magick_executable) if len(args.magick_executable) > 0 else "magick"

            # We need to undistort our images into ideal pinhole intrinsics.
            img_undist_cmd = (colmap_command + " image_undistorter \
                    --image_path " + args.source_path + "/input \
                    --input_path " + args.source_path + "/distorted/sparse/0 \
                    --output_path " + args.source_path + "\
                    --output_type COLMAP")
            exit_code = run_command(img_undist_cmd)
            if exit_code:
                self.status = 'error'
                raise Exception(f"Mapper failed with code {exit_code}")

            files = os.listdir(args.source_path + "/sparse")
            os.makedirs(args.source_path + "/sparse/0", exist_ok=True)
            # Copy each file from the source directory to the destination directory
            for file in files:
                if file == '0':
                    continue
                source_file = os.path.join(args.source_path, "sparse", file)
                destination_file = os.path.join(args.source_path, "sparse", "0", file)
                shutil.move(source_file, destination_file)

            if args.resize:
                print("Copying and resizing...")

                # Resize images.
                os.makedirs(args.source_path + "/images_2", exist_ok=True)
                os.makedirs(args.source_path + "/images_4", exist_ok=True)
                os.makedirs(args.source_path + "/images_8", exist_ok=True)
                # Get the list of files in the source directory
                files = os.listdir(args.source_path + "/images")
                # Copy each file from the source directory to the destination directory
                for file in files:
                    source_file = os.path.join(args.source_path, "images", file)

                    destination_file = os.path.join(args.source_path, "images_2", file)
                    shutil.copy2(source_file, destination_file)
                    exit_code = os.system(magick_command + " mogrify -resize 50% " + destination_file)
                    if exit_code != 0:
                        self.status = 'error'
                        raise Exception(f"50% resize failed with code {exit_code}. Exiting.")

                    destination_file = os.path.join(args.source_path, "images_4", file)
                    shutil.copy2(source_file, destination_file)
                    exit_code = os.system(magick_command + " mogrify -resize 25% " + destination_file)
                    if exit_code != 0:
                        self.status = 'error'
                        raise Exception(f"25% resize failed with code {exit_code}. Exiting.")

                    destination_file = os.path.join(args.source_path, "images_8", file)
                    shutil.copy2(source_file, destination_file)
                    exit_code = os.system(magick_command + " mogrify -resize 12.5% " + destination_file)
                    if exit_code != 0:
                        self.status = 'error'
                        raise Exception(f"12.5% resize failed with code {exit_code}. Exiting.")

        self.status = 'done'

# @right_menu_item('3DGS Args', '3D Gaussian Splatting')
# class Node3DGSArgs(NodeSimpleTemplate):
#     def __init__(self):
#         super().__init__(name='3DGS Args', width=200,
#                          input_names=['source path'],
#                          input_types=['str'],
#                          output_names=['colmap args'],
#                          output_types=['any'])
#         self.width = 240
#
#     def draw_parameters(self):
#         return False
#
#     def process(self):
#         from argparse import Namespace
#         epochs = 3000
#         resolution = -1
#         white_background = False
#         sh_degree = 3
#         densify_from_iter = 500
#         densify_until_iter = 15_000
#         densify_grad_threshold = 0.0002
#         loaded_iter = None  # None 表示从COLMAP点云创建， 数字表示从之前的训练结果创建
#         first_iter = None  # None 表示从loaded iter的轮次开始训练，否则则从指定的轮次开始， 该参数影响学习率等参数
#         args = Namespace(
#             sh_degree=sh_degree,
#             source_path=f"{data_root}/data/{scene_name}",
#             model_path=f"{data_root}/output/{output_name if output_name != '' else scene_name}",
#             images="images",
#             resolution=resolution,
#             white_background=white_background,
#             data_device="cuda",
#             eval=False,
#
#             iterations=epochs,
#             position_lr_init=0.00016,
#             position_lr_final=0.0000016,
#             position_lr_delay_mult=0.01,
#             position_lr_max_steps=30_000,
#             feature_lr=0.0025,
#             opacity_lr=0.05,
#             scaling_lr=0.005,
#             rotation_lr=0.001,
#             percent_dense=0.01,
#             lambda_dssim=0.2,
#             densification_interval=100,
#             opacity_reset_interval=3000,
#             densify_from_iter=densify_from_iter,
#             densify_until_iter=densify_until_iter,
#             densify_grad_threshold=densify_grad_threshold,
#             random_background=False,
#
#             convert_SHs_python=False,
#             compute_cov3D_python=False,
#             debug=False,
#
#             ip="127.0.0.1",
#             port=6009,
#             debug_from=-1,
#             detect_anomaly=False,
#             test_iterations=[epochs],
#             save_iterations=[epochs],
#             quiet=False,
#             checkpoint_iterations=[],
#             start_checkpoint=None,
#
#             loaded_iter=loaded_iter,
#             first_iter=first_iter if first_iter is not None else (loaded_iter if loaded_iter is not None else 0)
#         )
#         self.output[self.output_ids[0]] = colmap_args
