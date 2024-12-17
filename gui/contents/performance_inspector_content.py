import imgui

from gui.components import c
from gui.contents.base_content import BaseContent
from gui.global_app_state import g
from gui.modules import StyleModule, LayoutModule, FontModule, TextureModule, ChartModule
from gui.modules.cell_module import CellModule
from gui.user_data import user_settings


class DashBoard(BaseContent):
    _cell_module: CellModule = None

    @classmethod
    def c_init(cls):
        super().c_init()

        cls._cell_module = CellModule()
        cls._cell_module.register_cell("CPU Cell", cls._cpu_cell)
        cls._cell_module.add_cell_to_display_queue("CPU Cell")

    @classmethod
    def c_update(cls):
        super().c_update()

    @classmethod
    def c_show(cls):
        super().c_show()
        cls._cell_module.show()

    @classmethod
    def c_on_show(cls):
        super().c_on_show()
        g.mIsUserSettingsContentOpen = True

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()
        g.mIsUserSettingsContentOpen = False

    @classmethod
    def _cpu_cell(cls):
        ChartModule.draw_chart("fps")


class CPU(BaseContent):
    @classmethod
    def c_init(cls):
        super().c_init()

    @classmethod
    def c_update(cls):
        super().c_update()

    @classmethod
    def c_show(cls):
        super().c_show()

    @classmethod
    def c_on_show(cls):
        super().c_on_show()

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()


class GPU(BaseContent):
    @classmethod
    def c_init(cls):
        super().c_init()

    @classmethod
    def c_update(cls):
        super().c_update()

    @classmethod
    def c_show(cls):
        super().c_show()

    @classmethod
    def c_on_show(cls):
        super().c_on_show()

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()


class Memory(BaseContent):
    @classmethod
    def c_init(cls):
        super().c_init()

    @classmethod
    def c_update(cls):
        super().c_update()

    @classmethod
    def c_show(cls):
        super().c_show()

    @classmethod
    def c_on_show(cls):
        super().c_on_show()

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()


class PerformanceDebugger(BaseContent):
    @classmethod
    def c_init(cls):
        super().c_init()

    @classmethod
    def c_update(cls):
        super().c_update()

    @classmethod
    def c_show(cls):
        super().c_show()

    @classmethod
    def c_on_show(cls):
        super().c_on_show()

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()
