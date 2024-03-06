import imgui

from gui import components as c


class Cell:
    def __init__(self, name, func, allow_duplicate=False):
        self.name = name
        self.func = func
        self.allow_duplicate = allow_duplicate


class CellModule:
    def __init__(self):
        self.registered_cells: dict[str:Cell] = {}  # name: plugin
        self.displaying_cells: list[Cell] = []  # list[plugin]

    def register_cell(self, name, func, allow_duplicate=False):
        cell = Cell(name, func, allow_duplicate)
        self.registered_cells[name] = cell

    def add_cell_to_display_queue(self, name: str, idx=None):
        if idx is None:
            self.displaying_cells.append(self.registered_cells[name])
        else:
            self.displaying_cells.insert(idx, self.registered_cells[name])

    def move_plugin(self, plugin: Cell, idx):
        pass

    def show(self):
        if not self.displaying_cells:
            imgui.text('no cells')
            return
        for cell in self.displaying_cells:
            imgui.separator()
            c.bold_text(cell.name)
            cell.func()
            imgui.separator()
