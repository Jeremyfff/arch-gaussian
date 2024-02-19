from enum import Enum
from typing import Optional
from gui import global_var as g


class LayoutMode(Enum):
    flexible = 0
    fixed = 2


class LayoutDirection(Enum):
    Horizontal = 0
    Vertical = 1


class LayoutElement:
    def __init__(self, layout_name: str, parent: Optional['LayoutElement'], mode: LayoutMode, value: Optional[int]):
        self.parent = parent
        self.layout_name = layout_name
        self.children = []
        self.mode = mode
        self.value = value
        self.layout_direction = None
        self.size = (0, 0)
        self.pos = (0, 0)

    def set_layout_direction(self, direction: LayoutDirection):
        self.layout_direction = direction

    def add_child(self, layout_name: str, mode: LayoutMode, value: Optional[int]):
        layout = LayoutElement(layout_name, self, mode, value)
        self.children.append(layout)
        return layout

    def update_children_size(self):
        if not self.children:
            return
        horizontal = self.layout_direction == LayoutDirection.Horizontal
        total_value = self.size[0 if horizontal else 1]
        # get flexible size
        num_flexible = 0
        for child in self.children:
            if child.mode == LayoutMode.flexible:
                num_flexible += 1
        assert num_flexible > 0, 'must be at least one flexible'
        remain_value = total_value
        for child in self.children:
            if child.mode == LayoutMode.fixed:
                remain_value -= child.value
        flex_value = int(float(remain_value) / num_flexible)
        curr_pointer = self.pos
        for child in self.children:
            child.pos = curr_pointer
            if child.mode == LayoutMode.fixed:
                child.size = (child.value, self.size[1]) if horizontal else (self.size[0], child.value)
            elif child.mode == LayoutMode.flexible:
                child.size = (flex_value, self.size[1]) if horizontal else (self.size[0], flex_value)
            if horizontal:
                curr_pointer = (curr_pointer[0] + child.size[0], curr_pointer[1])
            else:
                curr_pointer = (curr_pointer[0], curr_pointer[1] + child.size[1])
        for child in self.children:
            child.update_children_size()


class LayoutScheme:
    def __init__(self, scheme_name):
        self.scheme_name = scheme_name
        self._size_dict = {}
        self._pos_dict = {}
        self.root_layout = LayoutElement('root', None, LayoutMode.fixed, 1)

        # add your layout here

        # remember to call self.update() after all init are done.

    def update(self):
        # update sizes
        self.root_layout.size = g.mWindowSize
        self.root_layout.update_children_size()

        # update _size_dict and _pos_dict
        children = self.root_layout.children
        while children:
            next_children = []
            for child in children:
                self._size_dict[child.layout_name] = child.size
                self._pos_dict[child.layout_name] = child.pos
                next_children += child.children
            children = next_children

    def get_pos(self, name):
        return self._pos_dict[name]

    def get_size(self, name):
        return self._size_dict[name]


def init():
    layout = LayoutScheme('main layout')
    style = g.mImguiStyle
    layout.root_layout.set_layout_direction(LayoutDirection.Vertical)
    layout.root_layout.add_child('level1_top', LayoutMode.fixed, g.FONT_SIZE + style.window_padding[1] * 2 + style.frame_padding[1] * 2)
    level1_mid = layout.root_layout.add_child('level1_mid', LayoutMode.flexible, 1)
    layout.root_layout.add_child('level1_bot', LayoutMode.fixed, g.FONT_SIZE + style.window_padding[1] * 2 + style.frame_padding[1] * 2)

    level1_mid.set_layout_direction(LayoutDirection.Horizontal)
    level1_mid.add_child('level2_left', LayoutMode.fixed, g.FONT_SIZE + style.window_padding[0] * 2 + style.frame_padding[0] * 2)
    level2_right = level1_mid.add_child('level2_right', LayoutMode.flexible, 1)

    level2_right.set_layout_direction(LayoutDirection.Horizontal)
    level2_right.add_child('level3_left', LayoutMode.fixed, 400)
    level3_right = level2_right.add_child('level3_right', LayoutMode.flexible, 1)  # main graphic view

    level3_right.set_layout_direction(LayoutDirection.Vertical)
    level3_right.add_child('level4_top', LayoutMode.flexible, 1)
    level3_right.add_child('level4_bot', LayoutMode.flexible, 1)
    layout.update()
    g.mLayoutScheme = layout


def on_resize():
    g.mLayoutScheme.update()
