import imgui

from gui import components as c


class Cell:
    def __init__(self, name, func, allow_duplicate=False, default_opened=True):
        self.name = name
        self.func = func
        self.allow_duplicate = allow_duplicate

        self.opened = default_opened

    def show(self):
        imgui.separator()
        imgui.push_id(f'{self.name}_arrow_button')
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, (0, 0))
        imgui.push_style_color(imgui.COLOR_BUTTON, 0, 0, 0, 0)
        if imgui.arrow_button('', imgui.DIRECTION_DOWN if self.opened else imgui.DIRECTION_RIGHT):
            self.opened = not self.opened
        imgui.pop_style_color()
        imgui.pop_style_var()
        imgui.pop_id()
        imgui.same_line()
        c.bold_text(self.name)
        if self.opened:
            self.func()
        imgui.separator()


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
            cell.show()
