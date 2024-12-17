from typing import Optional

import imgui

from gui.components import c
from gui.global_app_state import g

__runtime__ = True
if not __runtime__:
    from gui.modules.language_module import LanguageSet


class Cell:
    def __init__(self, name, func, allow_duplicate=False, default_opened=True, display_name=None):
        self.name = name
        self.display_name = display_name if display_name is not None else name
        self.func = func
        self.allow_duplicate = allow_duplicate

        self.opened = default_opened
        self.parent: Optional["CellModule"] = None

        self._curr_child_height = 0
        self._target_child_height = 0

    def __del__(self):
        pass

    def show(self):
        # imgui.separator()
        alpha = g.mImguiStyle.colors[imgui.COLOR_TEXT][3]  # Get Alpha for this cell, 使用Text是因为其他组件可能本身有alpha
        imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, 1, 1, 1, alpha * 0.04)
        c.begin_child_auto_height(f"{self.name}_region", width=imgui.get_content_region_available_width(), initial_height=0, border=True, flags=imgui.WINDOW_NO_SCROLLBAR)
        imgui.pop_style_color()
        # CHILD BEGIN =====================================================================
        imgui.push_style_color(imgui.COLOR_BUTTON, 0, 0, 0, 0)
        icon_name = 'caret-right' if not self.opened else 'caret-down'
        if c.icon_text_button(icon_name, self.display_name, imgui.get_content_region_available_width(), uid=f"icon_text_button_{icon_name}_{self.name}"):
            self.opened = not self.opened
        imgui.pop_style_color()
        if self.opened:
            self.func()
        c.end_child_auto_height(f"{self.name}_region")

    def update_display_name(self, new_display_name: str):
        self.display_name = new_display_name


class CellModule:
    def __init__(self, language_set: "LanguageSet" = None):
        """

        :param language_set: 当不为None时，启用自动翻译功能
        """
        self.registered_cells: dict[str:Cell] = {}  # name: plugin
        self.displaying_cells: list[Cell] = []  # list[plugin]
        self._l: Optional["LanguageSet"] = language_set
        if self._l is not None:
            from gui.modules import EventModule
            EventModule.register_language_change_callback(self._on_language_change)

    def __del__(self):
        if self._l is not None:
            from gui.modules import EventModule
            EventModule.unregister_language_change_callback(self._on_language_change)

    def _on_language_change(self):
        for name, cell in self.registered_cells.items():
            cell.update_display_name(self._l.get_translation(name))

    def register_cell(self, name, func, allow_duplicate=False):
        """
        注册cell， 注册后还需要执行add_cell_to_display_queue将cell添加到显示队列中。
        在新的content代码中，推荐使用下文的register_and_add_cell_to_display_queue同时实现注册和添加显示队列。
        """
        cell = Cell(name, func, allow_duplicate=allow_duplicate, default_opened=True, display_name=None if self._l is None else self._l.get_translation(name))
        cell.parent = self
        self.registered_cells[name] = cell

    def add_cell_to_display_queue(self, name: str, idx=None):
        """
        将cell添加到显示队列
        :param name: cell名称
        :param idx: 如果留空，则添加到末尾
        :return:
        """
        if idx is None:
            self.displaying_cells.append(self.registered_cells[name])
        else:
            self.displaying_cells.insert(idx, self.registered_cells[name])

    def register_and_add_cell_to_display_queue(self, name, func, allow_duplicate=False):
        """
        新版本推荐的注册cell并添加到显示队列的方法
        :param name: cell名称
        :param func: cell func
        :param allow_duplicate:
        :return:
        """
        self.register_cell(name, func, allow_duplicate)
        self.add_cell_to_display_queue(name)

    def move_plugin(self, plugin: Cell, idx):
        pass

    def show(self):
        if not self.displaying_cells:
            imgui.text('no cells')
            return
        for cell in self.displaying_cells:
            imgui.push_id(cell.name)
            cell.show()
            imgui.pop_id()

    def expand_all(self):
        for cell in self.registered_cells.values():
            cell.opened = True

    def collapse_all(self):
        for cell in self.registered_cells.values():
            cell.opened = False
