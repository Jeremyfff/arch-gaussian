import imgui

from gui.components import c
from gui.global_app_state import g
from gui.contents.pages.base_page import BasePage
from gui.contents.pages.full_page import FullPage
from gui.modules.cell_module import CellModule
from scripts.project_manager import ProjectManager


class HierarchyPage(FullPage):
    _inited = False
    page_name = 'hierarchy'
    cell_module = CellModule()

    @classmethod
    def p_init(cls):
        super().p_init()
        cls.cell_module.register_cell('GEOMETRIES', cls.geometry_collection_operation_panel_cell)
        cls.cell_module.register_cell('GAUSSIANS', cls.gaussian_collection_operation_panel_cell)
        cls.cell_module.add_cell_to_display_queue('GEOMETRIES')
        cls.cell_module.add_cell_to_display_queue('GAUSSIANS')

    @classmethod
    def p_call(cls):
        super().p_call()
