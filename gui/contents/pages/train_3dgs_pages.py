import logging
import os
import threading
from argparse import Namespace
from typing import Optional

import imgui

from gui import components as c
from gui import global_var as g
from gui.contents.pages.base_page import BasePage
from gui.modules import StyleModule, EventModule
from gui.modules.cell_module import CellModule
from gui.utils import io_utils
from scripts.project_manager import ProjectManager
from src.utils import progress_utils as pu


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
            cls.page_group.switch_page_obj(FullTrainingPage)
        if c.icon_text_button('meteor-line', 'basic training'):
            cls.page_group.switch_page_obj(BasicTrainingPage)
        if c.icon_text_button('menu-line', 'gaussian viewer'):
            cls.page_group.switch_page_obj(SimpleViewerPage)


class FullTrainingPage(BasePage):
    page_name = 'full training'
    page_level = 1
    cell_module = CellModule()

    ViewerContentModule: Optional[any] = None

    @classmethod
    def p_init(cls):
        cls.cell_module.register_cell('CONFIG', cls.config_cell)
        cls.cell_module.register_cell('FIX SCENE INFO', cls.fix_scene_cell)
        cls.cell_module.register_cell('IMPORT CAMERAS', cls.load_cameras_cell)
        cls.cell_module.register_cell('CREATE GAUSSIAN', cls.create_gaussian_cell)
        cls.cell_module.register_cell('POST SOCKET', cls.post_socket_cell)
        cls.cell_module.register_cell('GROUND TRUTH SOCKET', cls.gt_socket_cell)
        cls.cell_module.register_cell('LOSS SOCKET', cls.loss_socket_cell)
        cls.cell_module.register_cell('TRAIN GAUSSIAN', cls.train_gaussian_cell)
        cls.cell_module.register_cell('RESULT VIEWER', cls.result_viewer_cell)
        cls.cell_module.register_cell('OPERATION PANEL', cls.operation_panel_cell)

        cls.cell_module.add_cell_to_display_queue('CONFIG')
        cls.cell_module.add_cell_to_display_queue('FIX SCENE INFO')
        cls.cell_module.add_cell_to_display_queue('IMPORT CAMERAS')
        cls.cell_module.add_cell_to_display_queue('CREATE GAUSSIAN')
        cls.cell_module.add_cell_to_display_queue('POST SOCKET')
        cls.cell_module.add_cell_to_display_queue('GROUND TRUTH SOCKET')
        cls.cell_module.add_cell_to_display_queue('LOSS SOCKET')
        cls.cell_module.add_cell_to_display_queue('TRAIN GAUSSIAN')
        cls.cell_module.add_cell_to_display_queue('RESULT VIEWER')
        cls.cell_module.add_cell_to_display_queue('OPERATION PANEL')

        from gui.contents import ViewerContent
        cls.ViewerContentModule = ViewerContent

    @classmethod
    def p_call(cls):
        if not ProjectManager.curr_project.get_info('has_sparse0'):
            imgui.text('no sparse info')
            return
        cls.cell_module.show()

        if cls._is_fix_scene_complete_in_frame:
            cls._is_fix_scene_complete_in_frame = False
            EventModule.on_scene_manager_changed(cls._scene_manager)

        if cls._is_gaussian_changed_in_frame:
            cls._is_gaussian_changed_in_frame = False
            EventModule.on_gaussian_manager_changed(cls._gm)
        if cls._is_camera_manager_changed_in_frame:
            cls._is_camera_manager_changed_in_frame = False
            EventModule.on_camera_manager_changed(cls._cm)

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
        imgui.progress_bar(cls._fix_scene_progress, (imgui.get_content_region_available_width(), 10 * g.GLOBAL_SCALE))
        # if cls._fix_scene_output_msg:
        #     imgui.listbox('fix scene output', 0, cls._fix_scene_output_msg)

    @classmethod
    def load_cameras_cell(cls):
        if cls._is_loading_camera:
            StyleModule.push_disabled_button_color()
            imgui.button('LOAD CAMERAS(RUNNING...)')
        else:
            StyleModule.push_highlighted_button_color()
            if imgui.button('LOAD CAMERAS'):
                threading.Thread(target=cls._load_cameras).start()

        imgui.progress_bar(cls._load_camera_progress, (imgui.get_content_region_available_width(), 10 * g.GLOBAL_SCALE))
        StyleModule.pop_button_color()

    _create_gaussian_from_iter = 0
    _enable_create_gaussian_from_iter = False

    @classmethod
    def create_gaussian_cell(cls):
        imgui.text('create gaussian')
        if cls._is_creating_gaussian:
            StyleModule.push_disabled_button_color()
            imgui.button('CREATE GAUSSIAN(RUNNING...)')
        else:
            StyleModule.push_highlighted_button_color()
            if imgui.button('CREATE GAUSSIAN'):
                threading.Thread(target=cls._create_gaussian).start()
        StyleModule.pop_button_color()

    @classmethod
    def post_socket_cell(cls):
        imgui.text(f'has post socket = {cls._post_socket is not None}')
        cls._show_post_socket_editor()

    @classmethod
    def gt_socket_cell(cls):
        imgui.text('ground truth cell')

    @classmethod
    def loss_socket_cell(cls):
        imgui.text('loss socket cell')

    @classmethod
    def train_gaussian_cell(cls):
        imgui.text('train gaussian')
        if cls._is_training_gaussian:
            StyleModule.push_disabled_button_color()
            imgui.button('TRAIN(RUNNING...)')
        else:
            StyleModule.push_highlighted_button_color()
            if imgui.button('TRAIN'):
                threading.Thread(target=cls._train_gaussian).start()
        StyleModule.pop_button_color()
        imgui.progress_bar(cls._train_progress, (imgui.get_content_region_available_width(), 10 * g.GLOBAL_SCALE))

    _curr_selected_iteration_folder_idx = 0

    @classmethod
    def result_viewer_cell(cls):
        imgui.text('result viewer')
        if c.icon_text_button('refresh-line', 'Refresh Info'):
            ProjectManager.curr_project.scan_output()
            cls._curr_selected_iteration_folder_idx = 0
        output_iteration_folders: list = ProjectManager.curr_project.info['output_iteration_folder_names']
        output_iteration_folder_paths = ProjectManager.curr_project.info['output_iteration_folder_paths']
        changed, cls._curr_selected_iteration_folder_idx = imgui.listbox(
            '', cls._curr_selected_iteration_folder_idx,
            output_iteration_folders)
        if imgui.button('LOAD GAUSSIAN'):
            try:
                from src.manager.gaussian_manager import GaussianManager
                args = cls.gen_config_args()
                selected_folder_name = output_iteration_folders[cls._curr_selected_iteration_folder_idx]
                selected_folder_path = output_iteration_folder_paths[cls._curr_selected_iteration_folder_idx]
                loaded_iteration = int(selected_folder_name.replace('iteration_', ''))
                ply_path = os.path.join(selected_folder_path, 'point_cloud.ply')
                args.loaded_iter = loaded_iteration
                cls._gm = GaussianManager(args, scene_info=None, custom_ply_path=ply_path)
                cls._is_gaussian_changed_in_frame = True  # mark as True to call events
            except Exception as e:
                logging.error(e)
        if imgui.button('CREATE EMPTY GAUSSIAN SCENE'):
            cls._gm = None
            cls._is_gaussian_changed_in_frame = True

    @classmethod
    def operation_panel_cell(cls):
        imgui.text('operation panel')
        if cls.ViewerContentModule is None:
            imgui.text('no viewer content module')
            return
        cls.ViewerContentModule.operation_panel()

    # endregion

    # region config args

    @classmethod
    def _show_config_args_editor(cls):
        any_change = c.arg_editor(cls._args_dict, cls._args_type_dict)
        if cls._args is None or any_change:
            cls._args = cls.gen_config_args()

    @classmethod
    def gen_config_args(cls):
        args = Namespace(
            sh_degree=3,
            source_path=ProjectManager.curr_project.get_info('data_root'),
            model_path=ProjectManager.curr_project.get_info('output_root'),
            images="images",
            resolution=cls._args_dict['resolution'],
            white_background=cls._args_dict['white_background'],
            data_device="cuda",
            eval=False,

            iterations=cls._args_dict['epochs'],
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
            densify_from_iter=cls._args_dict['densify_from_iter'],
            densify_until_iter=cls._args_dict['densify_until_iter'],
            densify_grad_threshold=cls._args_dict['densify_grad_threshold'],
            random_background=False,

            convert_SHs_python=False,
            compute_cov3D_python=False,
            debug=False,

            ip="127.0.0.1",
            port=6009,
            debug_from=-1,
            detect_anomaly=False,
            test_iterations=[cls._args_dict['epochs']],
            save_iterations=[cls._args_dict['epochs']],
            quiet=False,
            checkpoint_iterations=[],
            start_checkpoint=None,

            loaded_iter=cls._args_dict['loaded_iter'],
            first_iter=cls._args_dict['first_iter'] if cls._args_dict['first_iter'] is not None else (
                cls._args_dict['loaded_iter'] if cls._args_dict['loaded_iter'] is not None else 0)
        )
        return args

    _args_dict = {
        'epochs': 3000,
        'resolution': -1,
        'white_background': False,
        'densify_from_iter': 500,
        'densify_until_iter': 15_000,
        'densify_grad_threshold': 0.0002,
        'loaded_iter': None,  # None 表示从COLMAP点云创建， 数字表示从之前的训练结果创建
        'first_iter': None,  # None 表示从loaded iter的轮次开始训练，否则则从指定的轮次开始， 该参数影响学习率等参数
    }
    _args_type_dict = {
        'epochs': c.ArgType.INTEGER,
        'resolution': c.ArgType.INTEGER,
        'white_background': c.ArgType.BOOLEAN,
        'densify_from_iter': c.ArgType.INTEGER,
        'densify_until_iter': c.ArgType.INTEGER,
        'densify_grad_threshold': c.ArgType.FLOAT,
        'loaded_iter': c.ArgType.OPTIONAL_INT,  # None 表示从COLMAP点云创建， 数字表示从之前的训练结果创建
        'first_iter': c.ArgType.OPTIONAL_INT,  # None 表示从loaded iter的轮次开始训练，否则则从指定的轮次开始， 该参数影响学习率等参数
    }
    _args = None

    # endregion

    # region fix scene

    _scene_manager = None
    _is_fixing_scene = False
    _is_fix_scene_complete_in_frame = False  # 在这帧内结束了线程
    _fix_scene_output_msg = []
    _fix_scene_progress = 0

    @classmethod
    def _fix_scene(cls):
        # in thread
        # 创建scene info
        if cls._args is None:
            cls._args = cls.gen_config_args()
        pu.create_contex('_fix_scene', cls._update_fix_scene_progress)
        pu.new_progress(3)
        cls._fix_scene_output_msg = []
        cls._is_fixing_scene = True

        with io_utils.OutputCapture(cls._fix_scene_output_msg):
            print(f'loading scene manager')
            pu.update(1)
            from src.manager.scene_manager import load_and_fix_scene
            pu.update(1)
            cls._scene_manager = load_and_fix_scene(cls._args)
            pu.update(1)
        cls._is_fixing_scene = False
        cls._is_fix_scene_complete_in_frame = True

    @classmethod
    def _update_fix_scene_progress(cls, value):
        cls._fix_scene_progress = value / pu.get_total()

    # endregion

    # region load cameras
    _cm = None
    _train_cameras = None
    _test_cameras = None
    _is_loading_camera = False
    _is_camera_manager_changed_in_frame = False
    _load_camera_progress = 0.0

    @classmethod
    def _load_cameras(cls):
        # in thread
        assert cls._scene_manager is not None
        assert cls._args is not None
        from src.manager.camera_manager import CameraManager

        pu.create_contex('cameraList_from_camInfos', cls._update_load_camera_progress)
        cls._is_loading_camera = True
        cls._cm = CameraManager()
        cls._train_cameras, cls._test_cameras = cls._cm.create_cameras(cls._args, cls._scene_manager.scene_info)
        cls._is_loading_camera = False
        cls._is_camera_manager_changed_in_frame = True

    @classmethod
    def _update_load_camera_progress(cls, value):
        cls._load_camera_progress = value / pu.get_total()

    # endregion

    # region create gaussian
    _gm = None
    _is_creating_gaussian = False
    _is_gaussian_changed_in_frame = False

    @classmethod
    def _create_gaussian(cls):
        # in thread
        assert cls._args is not None
        assert cls._scene_manager is not None
        from manager.gaussian_manager import GaussianManager
        cls._is_creating_gaussian = True
        cls._gm = GaussianManager(cls._args, cls._scene_manager.scene_info)
        logging.info(f"num points: {cls._gm.gaussians.get_xyz.shape[0]}")
        cls._is_creating_gaussian = False
        cls._is_gaussian_changed_in_frame = True

    # endregion

    # region sockets
    _is_generating_post_socket = False
    _enable_post_socket = True
    _post_socket = None
    _post_socket_camera_mode_list_str = ['RAW', 'STILL', 'ROTATE', 'SLOW_ROTATE']
    _post_socket_args_camera_mode_int = 3
    _post_socket_filename_mode_list_str = ['BY_ITERATION', 'BY_SNAP_COUNT']
    _post_socket_args_filename_mode_int = 1
    _post_socket_args_slow_ratio = 5.0
    _post_socket_args_folder_name = 'snapshots'
    _post_socket_args_iteration_gap = 100
    _post_socket_args_first_period_iteration_gap = 10
    _post_socket_args_first_period_end = 400

    @classmethod
    def _show_post_socket_editor(cls):
        changed, cls._enable_post_socket = imgui.checkbox('Enable Post Socket', cls._enable_post_socket)
        if changed:
            if not cls._enable_post_socket and cls._post_socket is not None:
                cls._post_socket = None
        if not cls._enable_post_socket:
            return
        # when enable post socket
        any_change = False
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._post_socket_args_camera_mode_int = imgui.combo(
            'Camera Mode', cls._post_socket_args_camera_mode_int, cls._post_socket_camera_mode_list_str)
        any_change |= changed
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._post_socket_args_filename_mode_int = imgui.combo(
            'Filename Mode', cls._post_socket_args_filename_mode_int, cls._post_socket_filename_mode_list_str
        )
        any_change |= changed
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._post_socket_args_slow_ratio = imgui.input_int('Slow Ratio', cls._post_socket_args_slow_ratio)
        any_change |= changed
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._post_socket_args_folder_name = imgui.input_text('Folder Name', cls._post_socket_args_folder_name)
        any_change |= changed
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._post_socket_args_iteration_gap = imgui.input_int('Iteration Gap',
                                                                       cls._post_socket_args_iteration_gap)
        any_change |= changed
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._post_socket_args_first_period_iteration_gap = imgui.input_int(
            'First Period Iteration Gap', cls._post_socket_args_first_period_iteration_gap
        )
        any_change |= changed
        imgui.set_next_item_width(imgui.get_content_region_available_width() / 2)
        changed, cls._post_socket_args_first_period_end = imgui.input_int(
            'First Period End', cls._post_socket_args_first_period_end
        )
        any_change |= changed
        if not cls._is_generating_post_socket:
            if cls._post_socket is None or any_change:
                cls._is_generating_post_socket = True
                threading.Thread(target=cls._gen_and_use_post_socket).start()
        else:
            # is generating
            imgui.text('generating post socket...')

    @classmethod
    def _gen_and_use_post_socket(cls):
        cls._post_socket = cls._gen_post_socket()

    @classmethod
    def _gen_post_socket(cls):
        cls._is_generating_post_socket = True

        from manager.train_manager import init_snapshot, take_snapshot, SnapshotCameraMode, SnapshotFilenameMode
        init_snapshot(0)

        def post_socket(**kwargs):
            """完成每一轮训练后的后处理内容"""
            _iteration = kwargs['iteration']
            take_snapshot(cls._cm, cls._gm,
                          _camera_mode=SnapshotCameraMode.SLOW_ROTATE,
                          _slow_ratio=5,
                          _filename_mode=SnapshotFilenameMode.BY_SNAP_COUNT,
                          _folder_name="snapshots",
                          _iteration_gap=100,
                          _first_period_iteration_gap=10,
                          _first_period_end=400,
                          **kwargs)
            _gaussians = kwargs['gaussians']
            if _iteration % 1000 == 0:
                print(_gaussians.get_xyz.shape)

        cls._is_generating_post_socket = False
        return post_socket

    @classmethod
    def _clear_post_socket(cls):
        cls._post_socket = None

    # endregion

    # region train
    _is_training_gaussian = False
    _train_gaussian_output_msg = []
    _train_progress = 0

    @classmethod
    def _train_gaussian(cls):
        assert cls._args is not None
        assert cls._gm is not None
        assert cls._cm is not None
        assert cls._scene_manager is not None
        pu.create_contex('train', cls._update_train_progress)
        cls._is_training_gaussian = True
        with io_utils.OutputCapture(cls._train_gaussian_output_msg):
            from manager.train_manager import train, init_output_folder
            init_output_folder(cls._args, cls._scene_manager.scene_info)
        train(cls._args, cls._scene_manager.scene_info, cls._gm.gaussians, cls._train_cameras,
              post_socket=cls._post_socket)
        cls._is_training_gaussian = False

    @classmethod
    def _update_train_progress(cls, value):
        cls._train_progress = value / pu.get_total()
    # endregion


class BasicTrainingPage(FullTrainingPage):
    _inited = False
    page_name = 'basic training'
    cell_module = CellModule()

    @classmethod
    def p_init(cls):
        cls.cell_module.register_cell('CONFIG', cls.config_cell)
        cls.cell_module.register_cell('FIX SCENE INFO', cls.fix_scene_cell)
        cls.cell_module.register_cell('IMPORT CAMERAS', cls.load_cameras_cell)
        cls.cell_module.register_cell('CREATE GAUSSIAN', cls.create_gaussian_cell)
        cls.cell_module.register_cell('TRAIN GAUSSIAN', cls.train_gaussian_cell)

        cls.cell_module.add_cell_to_display_queue('CONFIG')
        cls.cell_module.add_cell_to_display_queue('FIX SCENE INFO')
        cls.cell_module.add_cell_to_display_queue('IMPORT CAMERAS')
        cls.cell_module.add_cell_to_display_queue('CREATE GAUSSIAN')
        cls.cell_module.add_cell_to_display_queue('TRAIN GAUSSIAN')


class SimpleViewerPage(FullTrainingPage):
    _inited = False
    page_name = 'gaussian viewer'
    cell_module = CellModule()

    @classmethod
    def p_init(cls):
        cls.cell_module.register_cell('FIX SCENE INFO', cls.fix_scene_cell)
        cls.cell_module.register_cell('RESULT VIEWER', cls.result_viewer_cell)
        cls.cell_module.register_cell('OPERATION PANEL', cls.operation_panel_cell)
        cls.cell_module.add_cell_to_display_queue('FIX SCENE INFO')
        cls.cell_module.add_cell_to_display_queue('RESULT VIEWER')
        cls.cell_module.add_cell_to_display_queue('OPERATION PANEL')
        from gui.contents import ViewerContent
        cls.ViewerContentModule = ViewerContent