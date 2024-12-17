import imgui

from gui.components import c
from gui.global_app_state import g
from gui.contents.pages.base_page import BasePage
from gui.contents.pages.full_page import FullPage
from gui.modules.cell_module import CellModule
from scripts.project_manager import ProjectManager

__runtime__ = True
if not __runtime__:
    from gui.contents import ViewerContent

    raise Exception('this code will never be reached. ')


class Train3DGSMainPage(BasePage):
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
        if c.icon_text_button('rocket-2-fill', 'full training'):
            cls.parent_page_group.switch_page_obj(FullTrainingPage)
        if c.icon_text_button('meteor-line', 'basic training'):
            cls.parent_page_group.switch_page_obj(BasicTrainingPage)
        if c.icon_text_button('menu-line', 'gaussian viewer'):
            cls.parent_page_group.switch_page_obj(SimpleViewerPage)


class FullTrainingPage(FullPage):
    _inited = False
    page_name = 'full training'
    page_level = 1
    cell_module = CellModule()

    @classmethod
    def p_init(cls):
        super().p_init()
        cls.cell_module.register_cell('CONFIG', cls.config_cell)
        cls.cell_module.register_cell('FIX SCENE INFO', cls.scene_manager_cell)
        cls.cell_module.register_cell('IMPORT CAMERAS', cls.load_cameras_cell)
        cls.cell_module.register_cell('CREATE GAUSSIAN', cls.create_gaussian_cell)
        cls.cell_module.register_cell('POST SOCKET', cls.post_socket_cell)
        cls.cell_module.register_cell('GROUND TRUTH SOCKET', cls.gt_socket_cell)
        cls.cell_module.register_cell('LOSS SOCKET', cls.loss_socket_cell)
        cls.cell_module.register_cell('TRAIN GAUSSIAN', cls.train_gaussian_cell)
        cls.cell_module.register_cell('RESULT LOADER', cls.result_loader_cell)
        cls.cell_module.register_cell('RENDERER SETTINGS', cls.renderer_operation_panel_cell)

        cls.cell_module.add_cell_to_display_queue('CONFIG')
        cls.cell_module.add_cell_to_display_queue('FIX SCENE INFO')
        cls.cell_module.add_cell_to_display_queue('IMPORT CAMERAS')
        cls.cell_module.add_cell_to_display_queue('CREATE GAUSSIAN')
        cls.cell_module.add_cell_to_display_queue('POST SOCKET')
        cls.cell_module.add_cell_to_display_queue('GROUND TRUTH SOCKET')
        cls.cell_module.add_cell_to_display_queue('LOSS SOCKET')
        cls.cell_module.add_cell_to_display_queue('TRAIN GAUSSIAN')
        cls.cell_module.add_cell_to_display_queue('RESULT LOADER')
        cls.cell_module.add_cell_to_display_queue('RENDERER SETTINGS')

    @classmethod
    def p_call(cls):
        if not ProjectManager.curr_project.get_info('has_sparse0'):
            imgui.text('no sparse info')
            return
        super().p_call()


class BasicTrainingPage(FullPage):
    _inited = False
    page_name = 'basic training'
    page_level = 1
    cell_module = CellModule()

    @classmethod
    def p_init(cls):
        super().p_init()
        cls.cell_module.register_cell('CONFIG', cls.config_cell)
        cls.cell_module.register_cell('FIX SCENE INFO', cls.scene_manager_cell)
        cls.cell_module.register_cell('IMPORT CAMERAS', cls.load_cameras_cell)
        cls.cell_module.register_cell('CREATE GAUSSIAN', cls.create_gaussian_cell)
        cls.cell_module.register_cell('TRAIN GAUSSIAN', cls.train_gaussian_cell)

        cls.cell_module.add_cell_to_display_queue('CONFIG')
        cls.cell_module.add_cell_to_display_queue('FIX SCENE INFO')
        cls.cell_module.add_cell_to_display_queue('IMPORT CAMERAS')
        cls.cell_module.add_cell_to_display_queue('CREATE GAUSSIAN')
        cls.cell_module.add_cell_to_display_queue('TRAIN GAUSSIAN')

    @classmethod
    def p_call(cls):
        if not ProjectManager.curr_project.get_info('has_sparse0'):
            imgui.text('no sparse info')
            return
        super().p_call()


class SimpleViewerPage(FullPage):
    _inited = False
    page_name = 'gaussian viewer'
    cell_module = CellModule()

    @classmethod
    def p_init(cls):
        super().p_init()
        cls.cell_module.register_cell('RESULT LOADER', cls.result_loader_cell)
        cls.cell_module.register_cell('RENDERER SETTINGS', cls.renderer_operation_panel_cell)
        cls.cell_module.add_cell_to_display_queue('RESULT LOADER')
        cls.cell_module.add_cell_to_display_queue('RENDERER SETTINGS')

    @classmethod
    def p_call(cls):
        super().p_call()
