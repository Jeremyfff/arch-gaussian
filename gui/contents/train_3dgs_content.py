import threading
from argparse import Namespace

import imgui

from gui import components as c
from gui import global_var as g
from gui.contents.base_content import BaseContent
from gui.modules import StyleModule, EventModule
from gui.modules.animation_module import AnimatedPageGroup
from gui.modules.cell_module import CellModule
from gui.utils import io_utils
from scripts import project_manager as pm


class Train3DGSContent(BaseContent):
    _inited = False

    main_page_key = 'main'
    basic_training_page_key = 'basic_training'

    page_group = AnimatedPageGroup(vertical=True)
    cell_module = CellModule()

    @classmethod
    def c_init(cls):
        super().c_init()
        cls.page_group.add_page(cls.main_page_key, cls.main_page, page_level=0)
        cls.page_group.add_page(cls.basic_training_page_key, cls.basic_training_page, page_level=1)

        cls.cell_module.register_cell('CONFIG', cls.config_cell)
        cls.cell_module.register_cell('FIX SCENE INFO', cls.fix_scene_cell)
        cls.cell_module.register_cell('IMPORT CAMERAS', cls.import_cameras_cell)
        cls.cell_module.add_cell_to_display_queue('CONFIG')
        cls.cell_module.add_cell_to_display_queue('FIX SCENE INFO')
        cls.cell_module.add_cell_to_display_queue('IMPORT CAMERAS')

    @classmethod
    def c_update(cls):
        super().c_update()

    @classmethod
    def c_show(cls):
        super().c_show()
        if pm.curr_project is None:
            imgui.text('Please Open A Project First')
            return
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING,
                             (g.mImguiStyle.frame_padding[0] * 1.5, g.mImguiStyle.frame_padding[1] * 1.5))
        imgui.push_style_var(imgui.STYLE_ITEM_SPACING,
                             (g.mImguiStyle.item_spacing[0] * 1.5, g.mImguiStyle.item_spacing[1] * 1.5))
        cls.page_group.show_level_guide()
        cls.page_group.show()
        imgui.pop_style_var(2)

    @classmethod
    def c_on_show(cls):
        super().c_on_show()
        pass

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()
        pass
    # region page
    @classmethod
    def main_page(cls):
        with imgui.font(g.mFontBold):
            imgui.text('TRAIN 3D GAUSSIAN')
        if c.icon_text_button('rocket-2-fill', 'basic training'):
            cls.page_group.switch_page(cls.basic_training_page_key)

    @classmethod
    def basic_training_page(cls):
        if not pm.curr_project.get_info('has_sparse0'):
            imgui.text('no sparse info')
            return
        cls.cell_module.show()

    # endregion

    # region cells
    @classmethod
    def config_cell(cls):
        cls._show_config_args_editor()
        if imgui.button('SHOW ALL ARGS'):
            imgui.open_popup('args popup')
        if imgui.begin_popup('args popup'):
            imgui.begin_table('args info', 2, imgui.TABLE_ROW_BACKGROUND)
            imgui.table_next_column()
            if cls._args is not None:
                for key, value in vars(cls._args).items():
                    imgui.text(str(key))
                    imgui.table_next_column()
                    imgui.text(str(value))
                    imgui.table_next_column()
            imgui.end_table()
            imgui.end_popup()

    @classmethod
    def fix_scene_cell(cls):
        if cls._is_fixing_scene:
            StyleModule.push_disabled_button_color()
            imgui.button('LOAD AND FIX SCENE INFO(RUNNING...)')
        else:
            StyleModule.push_highlighted_button_color()
            if imgui.button('LOAD AND FIX SCENE INFO'):
                threading.Thread(target=cls._fix_scene).start()
        StyleModule.pop_button_color()
        if cls._fix_scene_output_msg:
            imgui.listbox('fix scene output', 0, cls._fix_scene_output_msg)
        if cls._is_fix_scene_complete_in_frame:
            cls._is_fix_scene_complete_in_frame = False
            EventModule.on_scene_manager_changed(cls._scene_manager)

    @classmethod
    def import_cameras_cell(cls):
        imgui.text('import cameras cell')

    # endregion

    # region config args
    _tint_color = (0.5, 0.5, 0.5, 0.5)

    @classmethod
    def easy_question_mark(cls, content):
        imgui.same_line()
        imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + g.mImguiStyle.frame_padding[1])
        c.icon_image('question-line', padding=True, tint_color=cls._tint_color)
        c.easy_tooltip(content)

    @classmethod
    def _show_config_args_editor(cls):
        any_change = False
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._epochs = imgui.input_int('epochs', cls._epochs, 1000, 1000)
        any_change |= changed
        cls.easy_question_mark('training epochs')
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._resolution = imgui.input_int('resolution', cls._resolution)
        any_change |= changed
        cls.easy_question_mark('default -1')
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._white_background = imgui.checkbox('white background', cls._white_background)
        any_change |= changed
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._sh_degree = imgui.input_int('sh degree', cls._sh_degree)
        any_change |= changed
        cls.easy_question_mark('default 3')
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._densify_from_iter = imgui.input_int('densify from iter', cls._densify_from_iter, 100)
        any_change |= changed
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._densify_until_iter = imgui.input_int('densify until iter', cls._densify_until_iter, 100)
        any_change |= changed
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._densify_grad_threshold = imgui.input_float('densify grad threshold', cls._densify_grad_threshold)
        any_change |= changed
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._imgui_enable_load_iter = imgui.checkbox('load from iter', cls._imgui_enable_load_iter)
        any_change |= changed
        if cls._imgui_enable_load_iter:
            imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
            changed, cls._imgui_load_iter_value = imgui.input_int('load iter', cls._imgui_load_iter_value)
            any_change |= changed
        cls._loaded_iter = cls._imgui_load_iter_value if cls._imgui_enable_load_iter else None

        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._imgui_enable_custom_first_iter = imgui.checkbox('custom first iter',
                                                                      cls._imgui_enable_custom_first_iter)
        any_change |= changed
        if cls._imgui_enable_custom_first_iter:
            imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
            changed, cls._imgui_custom_first_iter_value = imgui.input_int('first iter',
                                                                          cls._imgui_custom_first_iter_value)
            any_change |= changed
        cls._first_iter = cls._imgui_custom_first_iter_value if cls._imgui_enable_custom_first_iter else None
        if cls._args is None:
            cls._args = cls._gen_config_args()
        if any_change:
            cls._args = cls._gen_config_args()

    @classmethod
    def _gen_config_args(cls):
        args = Namespace(
            sh_degree=cls._sh_degree,
            source_path=pm.curr_project.get_info('data_root'),
            model_path=pm.curr_project.get_info('output_root'),
            images="images",
            resolution=cls._resolution,
            white_background=cls._white_background,
            data_device="cuda",
            eval=False,

            iterations=cls._epochs,
            position_lr_init=0.00016,
            position_lr_final=0.0000016,
            position_lr_delay_mult=0.01,
            position_lr_max_steps=30_000,
            feature_lr=0.0025,
            opacity_lr=0.05,
            scaling_lr=0.005,
            rotation_lr=0.001,
            percent_dense=0.01,
            lambda_dssim=0.2,
            densification_interval=100,
            opacity_reset_interval=3000,
            densify_from_iter=cls._densify_from_iter,
            densify_until_iter=cls._densify_until_iter,
            densify_grad_threshold=cls._densify_grad_threshold,
            random_background=False,

            convert_SHs_python=False,
            compute_cov3D_python=False,
            debug=False,

            ip="127.0.0.1",
            port=6009,
            debug_from=-1,
            detect_anomaly=False,
            test_iterations=[cls._epochs],
            save_iterations=[cls._epochs],
            quiet=False,
            checkpoint_iterations=[],
            start_checkpoint=None,

            loaded_iter=cls._loaded_iter,
            first_iter=cls._first_iter if cls._first_iter is not None else (
                cls._loaded_iter if cls._loaded_iter is not None else 0)
        )
        return args

    _epochs = 3000
    _resolution = -1
    _white_background = False
    _sh_degree = 3
    _densify_from_iter = 500
    _densify_until_iter = 15_000
    _densify_grad_threshold = 0.0002
    _imgui_enable_load_iter = False
    _imgui_load_iter_value = 0
    _loaded_iter = None  # None 表示从COLMAP点云创建， 数字表示从之前的训练结果创建
    _imgui_enable_custom_first_iter = False
    _imgui_custom_first_iter_value = 0
    _first_iter = None  # None 表示从loaded iter的轮次开始训练，否则则从指定的轮次开始， 该参数影响学习率等参数
    _args = None

    # endregion

    # region fix scene
    @classmethod
    def _fix_scene(cls):
        # in thread
        # 创建scene info
        assert cls._args is not None
        cls._fix_scene_output_msg = []
        cls._is_fixing_scene = True
        with io_utils.OutputCapture(cls._fix_scene_output_msg):
            print(f'loading scene manager')
            from src.manager.scene_manager import load_and_fix_scene
            cls._scene_manager = load_and_fix_scene(cls._args)
        cls._is_fixing_scene = False
        cls._is_fix_scene_complete_in_frame = True

    _scene_manager = None
    _is_fixing_scene = False
    _is_fix_scene_complete_in_frame = False  # 在这帧内结束了线程
    _fix_scene_output_msg = []

    # endregion

    # region load cameras
    @classmethod
    def _load_cameras(cls):
        # in thread
        assert cls._scene_manager is not None
        assert cls._args is not None
        from src.manager.camera_manager import CameraManager

        cls._is_loading_camera = True
        cm = CameraManager()
        cls._train_cameras, cls._test_cameras = cm.create_cameras(cls._args, cls._scene_manager)
        cls._is_loading_camera = False

    _train_cameras = None
    _test_cameras = None
    _is_loading_camera = False

    # endregion

    # region create gaussian
    @classmethod
    def _create_gaussian(cls):
        # in thread
        assert cls._args is not None
        assert cls._scene_manager is not None
        from manager.gaussian_manager import GaussianManager
        cls._is_creating_gaussian = True
        cls._gm = GaussianManager(cls._args, cls._scene_manager)
        print(f"num points: {cls._gm.gaussians.get_xyz.shape[0]}")
        cls._is_creating_gaussian = False

    _gm = None
    _is_creating_gaussian = False
    # endregion

    # region sockets

    # endregion

    # region train

    # endregion
