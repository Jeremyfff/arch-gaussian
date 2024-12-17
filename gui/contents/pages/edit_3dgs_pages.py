import imgui

from gui.components import c
from gui.global_app_state import g
from gui.contents.pages.base_page import BasePage
from gui.contents.pages.full_page import FullPage
from gui.modules.cell_module import CellModule

__runtime__ = True
if not __runtime__:
    raise Exception('this code will never be reached. ')


class Edit3DGSMainPage(BasePage):
    _inited = False
    page_name = 'main'
    page_level = 0

    @classmethod
    def p_init(cls):
        pass

    @classmethod
    def p_call(cls):
        with imgui.font(g.mFontBold):
            imgui.text('TRAIN 3D GAUSSIAN')
        if c.icon_text_button('rocket-2-fill', 'full edit'):
            cls.parent_page_group.switch_page_obj(FullEditPage)


class FullEditPage(FullPage):
    _inited = False
    page_name = 'full edit'
    page_level = 1
    cell_module = CellModule()
    @classmethod
    def p_init(cls):
        super().p_init()
        cls.cell_module.register_cell('RESULT LOADER', cls.result_loader_cell)
        cls.cell_module.register_cell('RENDERER SETTINGS', cls.renderer_operation_panel_cell)
        cls.cell_module.register_cell('EDIT GAUSSIAN COLLECTION', cls.gaussian_collection_operation_panel_cell)
        cls.cell_module.register_cell('EDIT GEOMETRY COLLECTION', cls.geometry_collection_operation_panel_cell)
        cls.cell_module.register_cell('CREATE MASKS', cls.mask_operation_panel_cell)
        cls.cell_module.register_cell('CREATE DATASET', cls.create_dataset_cell)
        cls.cell_module.register_cell('REPAINT', cls.repaint_cell)
        cls.cell_module.add_cell_to_display_queue('RESULT LOADER')
        cls.cell_module.add_cell_to_display_queue('RENDERER SETTINGS')
        cls.cell_module.add_cell_to_display_queue('EDIT GAUSSIAN COLLECTION')
        cls.cell_module.add_cell_to_display_queue('EDIT GEOMETRY COLLECTION')
        cls.cell_module.add_cell_to_display_queue('CREATE MASKS')
        cls.cell_module.add_cell_to_display_queue('CREATE DATASET')
        cls.cell_module.add_cell_to_display_queue('REPAINT')
    @classmethod
    def p_call(cls):
        super().p_call()
