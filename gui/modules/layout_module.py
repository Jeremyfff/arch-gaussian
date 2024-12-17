from enum import Enum
from typing import Optional

import imgui

from gui.components import c
from gui.global_app_state import g
from gui.modules.base_module import BaseModule


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

    def set_width(self, value):
        self.value = value

    def get_width(self):
        return self.value

    def set_height(self, value):
        self.value = value

    def get_height(self):
        return self.value


class LayoutScheme:
    def __init__(self, scheme_name):
        self.scheme_name = scheme_name

        self.root_layout = LayoutElement('root', None, LayoutMode.fixed, 1)

        self._child_dict: dict[str: LayoutElement] = {}  # 递归所有的child

        # add your layout here

        # remember to call self.update() after all init are done.

    def update(self):
        # update sizes
        self.root_layout.size = g.mWindowSize
        self.root_layout.update_children_size()

        # update _child_dict
        children = self.root_layout.children
        while children:
            next_children = []
            for child in children:
                self._child_dict[child.layout_name] = child
                next_children += child.children
            children = next_children

    def get_child(self, name):
        return self._child_dict[name]

    def get_pos(self, name):
        return self.get_child(name).pos

    def get_size(self, name):
        return self.get_child(name).size


class LayoutModule(BaseModule):
    layout: Optional[LayoutScheme] = None
    shadow_module = None

    @classmethod
    def m_init(cls):
        super().m_init()
        from gui.modules import ShadowModule
        cls.shadow_module = ShadowModule
        from gui.modules import EventModule
        EventModule.register_global_scale_change_callback(cls._on_global_scale_changed)

        style = g.mImguiStyle
        # create a default LayoutScheme
        cls.layout = LayoutScheme('main layout')
        # level1
        cls.layout.root_layout.set_layout_direction(LayoutDirection.Vertical)
        cls.layout.root_layout.add_child('level1_top', LayoutMode.fixed,
                                         g.font_size + style.window_padding[1] * 2 + style.frame_padding[1] * 2)
        level1_mid = cls.layout.root_layout.add_child('level1_mid', LayoutMode.flexible, 1)
        cls.layout.root_layout.add_child('level1_bot', LayoutMode.fixed,
                                         g.font_size + style.window_padding[1] * 2 + style.frame_padding[1] * 2)
        # level2
        level1_mid.set_layout_direction(LayoutDirection.Horizontal)
        nav_bar_width = g.font_size + style.window_padding[0] * 2 + style.frame_padding[0] * 2
        level1_mid.add_child('level2_left', LayoutMode.fixed,
                             nav_bar_width)
        level2_right = level1_mid.add_child('level2_right', LayoutMode.flexible, 1)

        # level3
        level2_right.set_layout_direction(LayoutDirection.Horizontal)
        level3_left = level2_right.add_child('level3_left', LayoutMode.fixed, 400 * g.global_scale)
        cls.vertical_resizable_layout = level3_left
        level2_right.add_child('level3_middle', LayoutMode.fixed, 2)
        level3_right = level2_right.add_child('level3_right', LayoutMode.flexible, 1)  # main graphic view

        # level4
        level3_right.set_layout_direction(LayoutDirection.Vertical)
        level3_right.add_child('level4_top', LayoutMode.flexible, 1)
        level3_right.add_child('level4_bot', LayoutMode.flexible, 1)
        cls.layout.update()

    @classmethod
    def on_resize(cls):
        cls.layout.update()

    @classmethod
    def _on_global_scale_changed(cls):
        cls.m_init()

    class LayoutWindow:
        """
        使用with 语句包裹，让其中内容成为layout布局的一部分
        with LayoutModule.LayoutWindow(your layout name, your window name, closable, flags):
            do something
        """
        default_flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
        default_flags |= imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE

        def __init__(self, layout_name, window_name=None, closable=False, flags=None):
            self.layout_name = layout_name
            self.window_name = layout_name if window_name is None else window_name
            self.window_closable = closable
            self.window_flags = LayoutModule.LayoutWindow.default_flags if flags is None else flags

        def __enter__(self):
            imgui.set_next_window_position(*LayoutModule.layout.get_pos(self.layout_name))
            imgui.set_next_window_size(*LayoutModule.layout.get_size(self.layout_name))
            imgui.begin(self.window_name, self.window_closable, self.window_flags)
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            # LayoutModule.shadow_module.draw_shadows()
            # we do not draw shadows here in the latest version
            # the drawing of shadows is now controlled by ui manager
            imgui.end()

    class LayoutChild:
        def __init__(self, layout_name, window_name=None, border=False):
            self.layout_name = layout_name
            self.window_name = layout_name if window_name is None else window_name
            self.border = border

        def __enter__(self):
            window_pos = imgui.get_window_position()
            pos = LayoutModule.layout.get_pos(self.layout_name)
            size = LayoutModule.layout.get_size(self.layout_name)
            imgui.set_cursor_pos((- window_pos[0] + pos[0],
                                  - window_pos[1] + pos[1]))
            c.begin_child(self.window_name, *size, border=self.border)
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            imgui.end_child()
