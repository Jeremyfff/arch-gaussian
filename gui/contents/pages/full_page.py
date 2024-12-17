import logging
import os
import random
import threading
import traceback
from abc import abstractmethod
from typing import Optional, Type

import imgui
import numpy as np

from gui.components import c
from gui.contents.pages.base_page import BasePage
from gui.global_app_state import g
from gui.modules import StyleModule, EventModule
from gui.modules.cell_module import CellModule
from gui.user_data import user_settings
from gui.utils import arg_utils, io_utils, name_utils, progress_utils as pu

from scripts.project_manager import ProjectDataKeys as pd
from scripts.project_manager import ProjectManager as pm

__runtime__ = True
if not __runtime__:
    from src.manager.camera_manager import CameraManager
    from src.manager.scene_manager import SceneManager
    from gui.contents import ViewerContent
    from src.manager.gaussian_manager import GaussianManager
    from gui.graphic.geometry import BaseGeometry
    from gui.graphic.geometry import WiredBoundingBox, SimpleCube
    from RePaint.repaint_manager import RepaintManager
    from scene.cameras import Camera
    raise Exception('this code will never be reached. ')


class FullPage(BasePage):
    """parent page of all functions"""
    _inited = False
    page_name = 'full page'
    page_level = 1
    cell_module = CellModule()

    ViewerContentClass: Type["ViewerContent"] = None

    @classmethod
    @abstractmethod
    def p_init(cls):
        from gui.contents import ViewerContent
        cls.ViewerContentClass = ViewerContent

    @classmethod
    @abstractmethod
    def p_call(cls):
        # Display UI
        cls.cell_module.show()

        # region handle events
        # fix scene complete => trigger on_scene_manager_changed
        if cls._is_fix_scene_complete_in_frame:
            cls._is_fix_scene_complete_in_frame = False
            EventModule.on_scene_manager_changed(cls._scene_manager)

        # gaussian_changed => trigger on_gaussian_manager_changed
        if cls._is_gaussian_changed_in_frame:
            cls._is_gaussian_changed_in_frame = False
            EventModule.on_gaussian_manager_changed(cls._gm)

        # camera_manager_changed => trigger on_camera_manager_changed
        if cls._is_camera_manager_changed_in_frame:
            cls._is_camera_manager_changed_in_frame = False
            EventModule.on_camera_manager_changed(cls._cm)
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
    def scene_manager_cell(cls):

        # region fix scene
        if cls._is_fixing_scene:
            StyleModule.push_disabled_button_color()
            imgui.button('LOAD AND FIX SCENE INFO(RUNNING...)')
        else:
            StyleModule.push_highlighted_button_color()
            if imgui.button('LOAD AND FIX SCENE INFO'):
                threading.Thread(target=cls._fix_scene).start()
        StyleModule.pop_button_color()
        pu.p_draw_progress_bar("fix_scene")

        # endregion
        if cls._scene_manager is None:
            imgui.text('No SceneManager')
            return
        imgui.text('SceneManager loaded')
        scene_info_train_cameras = cls._scene_manager.scene_info.train_cameras
        imgui.text(f'train_cameras num in scene info: [{len(scene_info_train_cameras)}]')
        if imgui.button("View Output Msgs"):
            imgui.open_popup("scene_manager_load_and_fix_scene_info_output")
        if imgui.begin_popup("scene_manager_load_and_fix_scene_info_output"):
            for line in cls._fix_scene_output_msg:
                imgui.text(line)
            imgui.end_popup()

    _imgui_curr_selected_camera_idx = 0

    @classmethod
    def load_cameras_cell(cls):
        # region load cameras
        if cls._is_loading_camera:
            StyleModule.push_disabled_button_color()
            imgui.button('LOAD CAMERAS(RUNNING...)')
        else:
            StyleModule.push_highlighted_button_color()
            if imgui.button('LOAD CAMERAS'):
                threading.Thread(target=cls._load_cameras).start()

        pu.p_draw_progress_bar("load_camera")
        StyleModule.pop_button_color()
        # endregion

        if cls._cm is None:
            imgui.text('No CameraManager')
            return
        imgui.text('CameraManager Loaded')

        resolution_scales = cls._cm.resolution_scales
        imgui.text(f'resolution_scales: {resolution_scales}')
        if resolution_scales[0] not in cls._cm.train_cameras.keys():
            imgui.text('waiting...')
            return
        sorted_cameras: list["Camera"] = cls._cm.sorted_cameras[resolution_scales[0]]
        imgui.text(f'loaded train_cameras: {len(sorted_cameras)}')
        changed, cls._imgui_curr_selected_camera_idx = imgui.slider_int(
            'camera idx', cls._imgui_curr_selected_camera_idx, 0, len(sorted_cameras) - 1)
        if changed:
            cls.ViewerContentClass.use_camera(sorted_cameras[cls._imgui_curr_selected_camera_idx])

        imgui.separator()
        imgui.text("debug region")
        if imgui.button("reduce cameras"):
            from scene.dataset_readers import CameraInfo
            sorted_cams: list[CameraInfo] = cls._cm.sorted_cameras[1.0]

            def select_objects(objects: list['CameraInfo'], num_objects: int):
                length = len(objects)

                if length <= num_objects:
                    return objects  # 如果列表长度小于等于要选择的对象数量，直接返回整个列表

                interval = length // num_objects
                selected_objects = [objects[0]]  # 选择第一个对象

                for i in range(1, num_objects):
                    index = min(i * interval, length - 1)  # 避免索引超出列表范围
                    selected_objects.append(objects[index])

                return selected_objects

            selected_cams: list[CameraInfo] = select_objects(sorted_cams, 10)
            for cam in selected_cams:
                print(cam.image_name)
            cls._cm.train_cameras[1.0] = selected_cams

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
        imgui.text(f'has ground truth cell = {cls._gt_socket is not None}')
        cls._show_gt_socket_editor()

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

        pu.p_draw_progress_bar("train_gaussian")

        if cls._is_training_gaussian:
            if imgui.button("Force Stop"):
                cls._cmd_dict['force_stop'] = 1
            imgui.same_line()
            if imgui.button("Stop and Save"):
                cls._cmd_dict['stop_and_save'] = 1

    _curr_selected_iteration_folder_idx = 0

    @classmethod
    def result_loader_cell(cls):
        imgui.text('Load File: ')
        # load gaussian from iteration
        gm = c.load_gaussian_from_iteration_button(uid="load_gaussian_from_iteration_button_in_full_page_result_loader_cell")
        if gm is not None:
            cls._gm = gm
            cls._is_gaussian_changed_in_frame = True  # mark as True to call events
        # load gaussian from custom file
        gm = c.load_gaussian_from_custom_file_button()
        if gm is not None:
            cls._gm = gm
            cls._is_gaussian_changed_in_frame = True  # mark as True to call events
        # create empty scene
        imgui.same_line()
        create_empty_scene = c.icon_text_button(
            'play-list-add-line', 'Create Empty Scene', width=imgui.get_content_region_available_width())
        if create_empty_scene:
            cls._gm = None
            cls._is_gaussian_changed_in_frame = True  # mark as True to call events

    @classmethod
    def renderer_operation_panel_cell(cls):
        if cls.ViewerContentClass is None:
            imgui.text('no viewer content module')
            return
        if cls.ViewerContentClass.mRenderer is None:
            imgui.text('no renderer')
            return
        cls.ViewerContentClass.mRenderer.operation_panel()

    @classmethod
    def scene_basic_geometry_collection_operatio_panel_cell(cls):
        if cls.ViewerContentClass is None:
            imgui.text('no viewer content module')
            return
        if cls.ViewerContentClass.mRenderer is None:
            imgui.text('no renderer')
            return
        cls.ViewerContentClass.mRenderer.show_scene_basic_geometry_collection_panel()

    @classmethod
    def geometry_collection_operation_panel_cell(cls):
        if cls.ViewerContentClass is None:
            imgui.text('no viewer content module')
            return
        if cls.ViewerContentClass.mRenderer is None:
            imgui.text('no renderer')
            return
        cls.ViewerContentClass.mRenderer.show_geometry_collection_panel()

    @classmethod
    def debug_collection_operation_panel_cell(cls):
        if cls.ViewerContentClass is None:
            imgui.text('no viewer content module')
            return
        if cls.ViewerContentClass.mRenderer is None:
            imgui.text('no renderer')
            return
        cls.ViewerContentClass.mRenderer.show_debug_collection_panel()

    @classmethod
    def gaussian_collection_operation_panel_cell(cls):
        if cls.ViewerContentClass is None:
            imgui.text('no viewer content module')
            return
        cls.ViewerContentClass.mRenderer.show_gaussian_collection_panel()

    _imgui_mask_creation_msg = ""
    _imgui_curr_editing_mask_name_idx = -1
    _imgui_curr_editing_mask_name_content = ""
    _imgui_mask_list_child_width = -1
    _imgui_curr_right_click_idx = -1
    _imgui_curr_selected_mask_wrappers = set()
    _imgui_mask_preview_enabled = False

    @classmethod
    def mask_operation_panel_cell(cls):
        if cls.ViewerContentClass is None:
            imgui.text('no viewer content module')
            return
        # region target gaussian group

        if imgui.button("select target gaussian"):
            imgui.open_popup("select target gaussian popup")
        if imgui.begin_popup("select target gaussian popup"):
            for i, gm in enumerate(cls.ViewerContentClass.mRenderer.gaussian_collection.gaussian_managers):
                clicked, _ = imgui.menu_item(gm.source_ply_path)  # TODO change to name
                if clicked:
                    cls._mask_target_gaussian = gm
                    imgui.close_current_popup()
            imgui.end_popup()
        imgui.same_line()
        if cls._mask_target_gaussian is None:
            c.warning_text("no target gaussian")
        else:
            c.text_with_max_length(cls._mask_target_gaussian.source_ply_path, 15)  # TODO change to name
        # endregion
        # region target mask geometry group

        if imgui.button("select geometry as mask"):
            imgui.open_popup("select target geometry as mask popup")
        if imgui.begin_popup("select target geometry as mask popup"):
            for i, geo in enumerate(cls.ViewerContentClass.mRenderer.geometry_collection.geometries):
                clicked, _ = imgui.menu_item(geo.name)
                if clicked:
                    cls._mask_target_geometry_as_mask = geo
                    imgui.close_current_popup()
            imgui.end_popup()
        imgui.same_line()
        if cls._mask_target_geometry_as_mask is None:
            c.warning_text("no geometry as mask")
        else:
            c.text_with_max_length(cls._mask_target_geometry_as_mask.name, 15)
        # endregion
        # region create mask button
        if cls._mask_target_gaussian is None or cls._mask_target_geometry_as_mask is None:
            StyleModule.push_disabled_button_color()
            c.icon_text_button("file-add-fill", "Create Mask", imgui.get_content_region_available_width(),
                               imgui.get_frame_height())
            StyleModule.pop_button_color()
        else:
            if c.icon_text_button("file-add-fill", "Create Mask"):

                success, msg = cls._create_mask_using_geometry(cls._mask_target_gaussian.gm,
                                                               cls._mask_target_geometry_as_mask)
                if not success:
                    cls._imgui_mask_creation_msg = msg
                    imgui.open_popup("create mask fail popup")
        if imgui.begin_popup_modal("create mask fail popup").opened:
            imgui.text(cls._imgui_mask_creation_msg)
            if imgui.button("ok"):
                imgui.close_current_popup()
            imgui.end_popup()

        # endregion
        # region masks list
        imgui.text("masks list:")
        c.begin_child("masks region",
                      height=max(
                          min(
                              g.global_scale * 300,
                              c.get_icon_double_text_button_height() * len(cls._gaussian_mask_wrappers)
                          ),
                          100 * g.global_scale))
        cls._imgui_mask_list_child_width = imgui.get_content_region_available_width()
        for i, mask_wrapper in enumerate(cls._gaussian_mask_wrappers):
            if cls._imgui_curr_editing_mask_name_idx == i:
                # region mask item (rename status)
                c.begin_child("mask rename region child", height=c.get_icon_double_text_button_height())
                imgui.push_id("input ok cancel for mask name editing")
                imgui.push_item_width(cls._imgui_mask_list_child_width / 2)
                changed, cls._imgui_curr_editing_mask_name_content = imgui.input_text("",
                                                                                      cls._imgui_curr_editing_mask_name_content)

                imgui.same_line()
                if imgui.button("ok"):
                    mask_wrapper.name = cls._imgui_curr_editing_mask_name_content
                    cls._imgui_curr_editing_mask_name_idx = -1
                imgui.same_line()
                if imgui.button("cancel"):
                    cls._imgui_curr_editing_mask_name_idx = -1
                imgui.pop_id()
                imgui.end_child()
                # endregion
            else:
                # region mask item (normal status)
                imgui.push_id(f'mask item {i}')
                if mask_wrapper in cls._imgui_curr_selected_mask_wrappers:
                    StyleModule.push_highlighted_button_color()
                c.icon_double_text_button("meteor-line", mask_wrapper.name,
                                          f"num points {mask_wrapper.num_points}"
                                          f"{', combined mask' if mask_wrapper.has_parent() else ''}",
                                          width=cls._imgui_mask_list_child_width)
                if mask_wrapper in cls._imgui_curr_selected_mask_wrappers:
                    StyleModule.pop_button_color()
                imgui.pop_id()
                if imgui.is_mouse_double_clicked(0) and imgui.is_item_hovered():
                    cls._imgui_curr_editing_mask_name_idx = i
                    cls._imgui_curr_editing_mask_name_content = mask_wrapper.name
                if imgui.is_mouse_clicked(imgui.MOUSE_BUTTON_RIGHT) and imgui.is_item_hovered():
                    cls._imgui_curr_right_click_idx = i
                    imgui.open_popup(f"named mask right click popup")
                if imgui.is_mouse_clicked(imgui.MOUSE_BUTTON_LEFT) and imgui.is_item_hovered():
                    if g.mShiftDown:
                        # shift按下时
                        if mask_wrapper in cls._imgui_curr_selected_mask_wrappers:
                            cls._imgui_curr_selected_mask_wrappers.remove(mask_wrapper)
                        else:
                            cls._imgui_curr_selected_mask_wrappers.add(mask_wrapper)
                    elif g.mCtrlDown:
                        # ctrl按下时
                        cls._imgui_curr_selected_mask_wrappers.add(mask_wrapper)
                    else:
                        cls._imgui_curr_selected_mask_wrappers.clear()
                        cls._imgui_curr_selected_mask_wrappers.add(mask_wrapper)

                # endregion
        # endregion
        # region mask right click menu
        if imgui.begin_popup(f"named mask right click popup"):
            i = cls._imgui_curr_right_click_idx
            mask_wrapper = cls._gaussian_mask_wrappers[i]
            mask = mask_wrapper.mask
            gm = cls._mask_target_gaussian.gm
            # region 每个右键对象都有的内容
            if imgui.menu_item("rename")[0]:
                cls._imgui_curr_editing_mask_name_idx = i
                cls._imgui_curr_editing_mask_name_content = mask_wrapper.name
                imgui.close_current_popup()
            if imgui.menu_item("delete")[0]:
                gm.restore()
                cls._gaussian_mask_wrappers.pop(i)
                if mask_wrapper in cls._imgui_curr_selected_mask_wrappers:
                    cls._imgui_curr_selected_mask_wrappers.remove(mask_wrapper)
                imgui.close_current_popup()
            clicked, cls._imgui_mask_preview_enabled = imgui.checkbox("preview", cls._imgui_mask_preview_enabled)
            if clicked:
                if cls._imgui_mask_preview_enabled:
                    gm.cache()
                    gm.paint_by_mask(mask)
                else:
                    gm.restore()
            if imgui.menu_item("restore")[0]:
                gm.restore()
                imgui.close_current_popup()
            # endregion
            # region 当wrapper不是combined类型时额外的内容
            imgui.separator()
            if imgui.menu_item("update")[0]:
                mask_wrapper.create_mask_by_parent()
                imgui.close_current_popup()
            # endregion
            # region 当右键在了多选内容上时额外的内容
            if len(cls._imgui_curr_selected_mask_wrappers) > 1 and mask_wrapper in cls._imgui_curr_selected_mask_wrappers:
                imgui.separator()
                if imgui.menu_item("combine masks")[0]:
                    cls._combine_selected_masks(False)
                if imgui.menu_item("combine masks(delete origins)")[0]:
                    cls._combine_selected_masks(True)
            # endregion
            imgui.end_popup()
        if not imgui.is_popup_open("named mask right click popup") and cls._imgui_mask_preview_enabled:
            cls._imgui_mask_preview_enabled = False
            cls._mask_target_gaussian.gm.restore()
        imgui.end_child()
        # endregion

    _imgui_preview_boundary_bbox: bool = False
    _imgui_preview_ground_cube: bool = False
    _imgui_create_dataset_stop_signal = False
    _imgui_is_creating_dataset = False
    _imgui_create_dataset_coroutine = None

    @classmethod
    def create_dataset_cell(cls):
        if cls.ViewerContentClass is None:
            imgui.text('no viewer content module')
            return
        # region mask boundary debug bbox
        _, cls._imgui_preview_boundary_bbox = imgui.checkbox("preview boundary bbox", cls._imgui_preview_boundary_bbox)
        imgui.same_line()
        if imgui.button("regenerate boundary bbox"):
            cls._mask_boundary_debug_bbox = None
        if cls._mask_boundary_debug_bbox is None:
            # cls.create_mask_boundary_debug_bbox()
            pass
        if cls._imgui_preview_boundary_bbox:
            cls.ViewerContentClass.mRenderer.debug_collection.draw_bbox(cls._mask_boundary_debug_bbox,
                                                                        skip_examine=True)
        if cls._mask_boundary_warning_msg != '':
            c.warning_text(cls._mask_boundary_warning_msg)

        if cls._mask_boundary_debug_bbox is not None:
            bbox: "WiredBoundingBox" = cls._mask_boundary_debug_bbox
            changed, bound_min = imgui.drag_float3("bound_min", *bbox.bound_min,
                                                   user_settings.move_scroll_speed)
            if changed:
                cls._mask_boundary_debug_bbox.set_bound_min(bound_min)
                pm.curr_project.set_project_data(pd.MASK_BOUNDARY_DEBUG_BBOX_MIN, bound_min)
            changed, bound_max = imgui.drag_float3("bound_max", *bbox.bound_max,
                                                   user_settings.scale_scroll_speed)
            if changed:
                cls._mask_boundary_debug_bbox.set_bound_max(bound_max)
                pm.curr_project.set_project_data(pd.MASK_BOUNDARY_DEBUG_BBOX_MAX, bound_max)

        # endregion
        # region ground cube
        _, cls._imgui_preview_ground_cube = imgui.checkbox("preview ground", cls._imgui_preview_ground_cube)
        if cls._mask_ground_debug_cube is None:
            cls.create_mask_ground_debug_cube()
        if cls._imgui_preview_ground_cube:
            cls.ViewerContentClass.mRenderer.debug_collection.draw_cube(cls._mask_ground_debug_cube, skip_examine=True)
        if cls._mask_ground_debug_cube is not None:
            cube: "SimpleCube" = cls._mask_ground_debug_cube
            changed, cls._ground_height = imgui.drag_float("ground height", cls._ground_height,
                                                           user_settings.move_scroll_speed)
            if changed:
                cube.translation = (0, 0, cls._ground_height)
                pm.curr_project.set_project_data(pd.GROUND_HEIGHT, cls._ground_height)
        # endregion
        # region settings
        imgui.separator()
        cls.show_dataset_creation_config()
        # endregion

        # region create dataset button
        imgui.separator()
        if cls._imgui_is_creating_dataset:
            StyleModule.push_disabled_button_color()
            if cls._imgui_create_dataset_stop_signal:
                content = "GENERATE DATASET(Stopping...)"
            else:
                content = "GENERATE DATASET(Running...)"
            imgui.button(content, imgui.get_content_region_available_width(), imgui.get_frame_height_with_spacing())
            StyleModule.pop_button_color()
            if imgui.button("STOP", imgui.get_content_region_available_width(), imgui.get_frame_height_with_spacing()):
                cls._imgui_create_dataset_stop_signal = True

        else:
            StyleModule.push_highlighted_button_color()
            if imgui.button("GENERATE DATASET", imgui.get_content_region_available_width(),
                            imgui.get_frame_height_with_spacing()):
                cls._imgui_create_dataset_coroutine = cls.create_dataset()
                cls._imgui_is_creating_dataset = True
            StyleModule.pop_button_color()
        if cls._imgui_is_creating_dataset:
            try:
                next(cls._imgui_create_dataset_coroutine)
            except (StopIteration, RuntimeError):
                print("创建dataset结束")
                cls._imgui_is_creating_dataset = False
                cls.on_create_dataset_stop()
            # endregion

    _bw_threshold = 0.5
    _rm: Optional["RepaintManager"] = None

    @classmethod
    def repaint_cell(cls):
        imgui.text("repaint cell")
        try:
            # if cls._gm is None:
            #     c.warning_text("no gaussian manager, please load gaussian first")
            #     return
            # if not len(cls._gaussian_mask_wrappers):
            #     c.warning_text("no gaussian mask wrapper, please create one first")
            #     return
            if imgui.button("set camera"):
                mRenderer = cls.ViewerContentClass.mRenderer
                camera = mRenderer.camera
                camera.target = (0, 0, 0)
                camera.radius = 2
                camera.angle_x = -30
                camera.angle_y = -135
                camera.update()
            if imgui.button("cache gaussian"):
                cls._gm.cache()
                print("gaussian cached")
            if imgui.button("restore gaussian"):
                cls._gm.restore()
                print("gaussian restored")

            if imgui.button("take snapshot"):
                print("take snapshot button pressed")
                mRenderer = cls.ViewerContentClass.mRenderer
                camera = mRenderer.camera

                if len(cls._imgui_curr_selected_mask_wrappers):
                    mask_wrapper = list(cls._imgui_curr_selected_mask_wrappers)[0]
                    print("use first selected gaussian mask wrapper")
                else:
                    mask_wrapper = cls._gaussian_mask_wrappers[0]
                    print("use first gaussian mask wrapper by default")

                cls._gm.cache()

                result = cls._gm.render(camera, convert_to_pil=True)
                result.save("./_debug_gt.png")

                cls._gm.paint_by_mask(mask_wrapper.mask)

                result = cls._gm.render(camera, convert_to_rgb_arr=True)
                print(result.shape)
                red_channel = result[:, :, 0]
                # 设置阈值，大于0.5的设为255（白色），小于等于0.5的设为0（黑色）
                _, cls._bw_threshold = imgui.slider_float("threshold for bw", cls._bw_threshold, 0.0, 1.0)

                bw_image = np.where(red_channel / 255 > cls._bw_threshold, 255, 0)
                from PIL import Image
                # 创建新的 PIL 图像并保存
                output_image = Image.fromarray(bw_image.astype(np.uint8))
                output_image.save("./_bw_mask.png")

                cls._gm.restore()
            if imgui.button("repaint test (raw)"):
                """
                使用原始方法测试
                """
                from RePaint.repaint_manager import RepaintManager
                cls._rm = RepaintManager()
                cls._rm.raw_run()

            if imgui.button("repaint test (sample)"):
                from RePaint.repaint_manager import RepaintManager
                cls._rm = RepaintManager()
                cls._rm.prepare_work()
                dl = cls._rm.dl
                print("getting batch")
                batch = next(iter(dl))
                gt = batch['GT']
                gt_keep_mask = batch.get('gt_keep_mask')

                cls._rm.run(gt, gt_keep_mask)




        except Exception as e:
            traceback.print_exc()

    # endregion

    # region config args

    @classmethod
    def _show_config_args_editor(cls):
        any_change = c.arg_editor(arg_utils.args_dict, arg_utils.args_type_dict)
        if cls._args is None or any_change:
            cls._args = arg_utils.gen_config_args()

    _args = None

    # endregion

    # region fix scene
    if not __runtime__:
        from src.manager.scene_manager import SceneManager
    _scene_manager: Optional['SceneManager'] = None
    _is_fixing_scene = False
    _is_fix_scene_complete_in_frame = False  # 在这帧内结束了线程
    _fix_scene_output_msg = []

    @classmethod
    def _fix_scene(cls):
        # in thread
        # 创建scene info
        if cls._args is None:
            cls._args = arg_utils.gen_config_args()
        pu.p_create_contex("fix_scene")
        pu.p_new_progress("fix_scene", 3)
        cls._fix_scene_output_msg = []
        cls._is_fixing_scene = True

        with io_utils.OutputCapture(cls._fix_scene_output_msg):
            print(f'loading scene manager')
            pu.p_update("fix_scene", 1)
            from src.manager.scene_manager import load_and_fix_scene
            pu.p_update("fix_scene", 1)
            cls._scene_manager = load_and_fix_scene(cls._args)
            pu.p_update("fix_scene", 1)
        cls._is_fixing_scene = False
        cls._is_fix_scene_complete_in_frame = True


    # endregion

    # region load cameras

    _cm: Optional['CameraManager'] = None
    _is_loading_camera: bool = False
    _is_camera_manager_changed_in_frame: bool = False

    @classmethod
    def _load_cameras(cls):
        # in thread
        assert cls._scene_manager is not None
        assert cls._args is not None
        cls._is_loading_camera = True
        from src.manager.camera_manager import CameraManager
        pu.p_create_contex("load_camera", "Loading Camera Infos")
        cls._cm = CameraManager()
        cls._cm.create_cameras(cls._args, cls._scene_manager.scene_info)
        cls._is_loading_camera = False
        cls._is_camera_manager_changed_in_frame = True


    # endregion

    # region create gaussian

    _gm: Optional["GaussianManager"] = None
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

    _is_generating_gt_socket = False
    _enable_gt_socket = True
    _gt_socket = None

    @classmethod
    def _show_gt_socket_editor(cls):
        changed, cls._enable_gt_socket = imgui.checkbox('Enable Ground Truth Socket', cls._enable_gt_socket)
        if changed:
            if not cls._enable_gt_socket and cls._gt_socket is not None:
                cls._gt_socket = None
        if not cls._enable_gt_socket:
            return

        any_change = False
        if not cls._is_generating_gt_socket:
            if cls._gt_socket is None or any_change:
                cls._is_generating_gt_socket = True
                threading.Thread(target=cls._gen_and_use_gt_socket()).start()
        else:
            # is generating
            imgui.text('generating gt socket...')

    @classmethod
    def _gen_and_use_gt_socket(cls):
        cls._gt_socket = cls._gen_gt_socket()

    @classmethod
    def _gen_gt_socket(cls):
        cls._is_generating_gt_socket = True
        import torch
        def gt_socket(**kwargs):
            viewpoint_cam = kwargs['viewpoint_cam']
            image = viewpoint_cam.original_image.cuda()
            iteration = kwargs['iteration']
            # print(f"iter {iteration}: image shape = {image.shape}, image_type = {type(image)}")
            # 将彩色图像转换为灰度图像
            with torch.no_grad():
                gray_img = torch.mean(image, dim=0, keepdim=True)  # 求取每个像素的 RGB 通道平均值，得到灰度图像
                gray_img = torch.cat([gray_img, gray_img, gray_img], dim=0)
            return gray_img

        cls._is_generating_gt_socket = False
        return gt_socket

    # endregion

    # region train
    _is_training_gaussian = False
    _train_gaussian_output_msg = []
    _default_cmd_dict = {"force_stop": 0,
                         "stop_and_save": 0
                         }
    _cmd_dict = {}

    @classmethod
    def _train_gaussian(cls):
        assert cls._args is not None
        assert cls._gm is not None
        assert cls._cm is not None
        assert cls._scene_manager is not None
        pu.p_create_contex("train_gaussian", "Train Gaussian")
        cls._cmd_dict = cls._default_cmd_dict.copy()
        cls._is_training_gaussian = True
        with io_utils.OutputCapture(cls._train_gaussian_output_msg):
            from manager.train_manager import train, init_output_folder
            init_output_folder(cls._args, cls._scene_manager.scene_info)
        train(cls._args, cls._scene_manager.scene_info, cls._gm.gaussians, cls._cm.train_cameras,
              gt_socket=cls._gt_socket,
              post_socket=cls._post_socket,
              cmd_dict=cls._cmd_dict)
        cls._is_training_gaussian = False

    # endregion

    # region mask
    _mask_target_gaussian = None

    _mask_target_geometry_as_mask = None

    _gaussian_mask_wrappers: list["GaussianMaskWrapper"] = []

    @classmethod
    def _gen_mask_wrapper_name(cls):
        next_num = name_utils.get_next_name_idx([a.name for a in cls._gaussian_mask_wrappers])
        return f"mask_{next_num}"

    @classmethod
    def _create_mask_using_geometry(cls, target_gaussian_manager: "GaussianManager",
                                    target_geometry_as_mask: "BaseGeometry") -> tuple[bool, str]:
        """

        :param target_gaussian_manager:
        :param target_geometry_as_mask:
        :return: 是否创建成功, 信息
        """
        mask_wrapper = GaussianMaskWrapper(cls._gen_mask_wrapper_name(),
                                           target_gaussian_manager, target_geometry_as_mask)
        success, msg = mask_wrapper.create_mask_by_parent()
        if success:
            cls._gaussian_mask_wrappers.append(mask_wrapper)
        return success, msg

    @classmethod
    def _combine_selected_masks(cls, delete_org_masks):
        from src.manager.gaussian_manager import GaussianManager
        combined_mask = GaussianManager.combine_masks([a.mask for a in cls._imgui_curr_selected_mask_wrappers])
        combined_mask_wrapper = GaussianMaskWrapper(cls._gen_mask_wrapper_name(), None, None)
        combined_mask_wrapper.assign_mask(combined_mask)
        cls._gaussian_mask_wrappers.append(combined_mask_wrapper)
        if delete_org_masks:
            for mask_wrapper in cls._imgui_curr_selected_mask_wrappers:
                cls._gaussian_mask_wrappers.remove(mask_wrapper)
            cls._imgui_curr_selected_mask_wrappers.clear()

    # endregion

    # region create dataset
    _mask_boundary_debug_bbox: Optional["WiredBoundingBox"] = None
    _mask_ground_debug_cube: Optional["SimpleCube"] = None
    _ground_height = 0.0
    _mask_boundary_warning_msg = ''
    _dataset_creation_settings_default = {
        "num_masks": 100,
        "mask_size_min": 0.1,
        "mask_size_max": 0.5,
        "camera_angle_y_min": -175.0,
        "camera_angle_y_max": -135.0,
        "camera_radius_min": 1.0,
        "camera_radius_max": 5.0,
        "angle_x_sample": 18,
        "angle_y_sample": 4,
        "radius_sample": 4,
        "enable_pix2pix_output": True
    }
    _dataset_creation_settings = {}

    _dataset_creation_settings_type_dict = {
        "num_masks": arg_utils.ArgType.INTEGER,
        "mask_size_min": arg_utils.ArgType.FLOAT,
        "mask_size_max": arg_utils.ArgType.FLOAT,
        "camera_angle_y_min": arg_utils.ArgType.FLOAT,
        "camera_angle_y_max": arg_utils.ArgType.FLOAT,
        "camera_radius_min": arg_utils.ArgType.FLOAT,
        "camera_radius_max": arg_utils.ArgType.FLOAT,
        "angle_x_sample": arg_utils.ArgType.INTEGER,
        "angle_y_sample": arg_utils.ArgType.INTEGER,
        "radius_sample": arg_utils.ArgType.INTEGER,
        "enable_pix2pix_output": arg_utils.ArgType.BOOLEAN
    }

    @classmethod
    def create_mask_boundary_debug_bbox(cls):
        raise NotImplementedError
        # from gui.graphic.geometry import WiredBoundingBox
        # # region calculate bounds when there is no data in project manager.project_data
        # bbox_min = pm.curr_project.get_project_data(pd.MASK_BOUNDARY_DEBUG_BBOX_MIN, None)
        # bbox_max = pm.curr_project.get_project_data(pd.MASK_BOUNDARY_DEBUG_BBOX_MAX, None)
        # # endregion
        # # region calculate bbox if no bbox data in project data
        # if bbox_min is None or bbox_max is None:
        #     bounds: list[tuple] = []
        #     need_warning = False
        #     for i, gm in enumerate(cls.ViewerContentClass.mRenderer.gaussian_collection.gaussian_managers):
        #         gm: "GaussianManager" = gm
        #         if gaussian_point_cloud.debug_bbox is not None:
        #             bounds.append(gaussian_point_cloud.debug_bbox.bound_min)
        #             bounds.append(gaussian_point_cloud.debug_bbox.bound_max)
        #             if sum(gaussian_point_cloud.transition) != 0:
        #                 need_warning |= True
        #     bounds_arr = np.array(bounds)
        #     # 计算边界框的最小值和最大值
        #     bbox_min = np.min(bounds_arr, axis=0)
        #     bbox_max = np.max(bounds_arr, axis=0)
        #     if need_warning:
        #         cls._mask_boundary_warning_msg = "one or more Gaussian point cloud bounding boxes has been detected to be not at the origin, \n" \
        #                                          "which may lead to errors when calculating the bounding boxes of all Gaussians. \n" \
        #                                          "Please ensure that the translation of all Gaussians is at the origin."
        #     else:
        #         cls._mask_boundary_warning_msg = ''
        # # endregion
        # cls._mask_boundary_debug_bbox = WiredBoundingBox("_random_mask_boundary_bbox", bbox_min, bbox_max)

    @classmethod
    def create_mask_ground_debug_cube(cls):
        cls._ground_height = pm.curr_project.get_project_data(pd.GROUND_HEIGHT, cls._ground_height)

        from gui.graphic.geometry import SimpleCube
        cls._mask_ground_debug_cube = SimpleCube("_mask_ground_debug_cube", size=(10, 10, 0.01), )
        cls._mask_ground_debug_cube.translation = (0, 0, cls._ground_height)

    @classmethod
    def show_dataset_creation_config(cls):
        c.arg_editor(cls._dataset_creation_settings, cls._dataset_creation_settings_type_dict)

    _tmp_geo_as_mask: Optional["SimpleCube"] = None
    _parameters_before_create_dataset = {}  # 保存了在创建dataset前的参数

    @classmethod
    def create_dataset(cls):
        from PIL import Image
        mRenderer = cls.ViewerContentClass.mRenderer
        opt = cls._dataset_creation_settings
        # region 保存初始参数
        cls._parameters_before_create_dataset["raw_enable_render_gaussians"] = mRenderer.render_gaussians
        cls._parameters_before_create_dataset["raw_enable_render_geometries"] = mRenderer.render_geometries
        cls._parameters_before_create_dataset["raw_enable_render_debug_geometries"] = mRenderer.render_debug_geometries
        cls._parameters_before_create_dataset["preview_boundary_bbox"] = cls._imgui_preview_boundary_bbox
        cls._parameters_before_create_dataset["preview_ground_cube"] = cls._imgui_preview_ground_cube
        cls._parameters_before_create_dataset["image_width"] = mRenderer.width
        cls._parameters_before_create_dataset["image_height"] = mRenderer.height
        cls._parameters_before_create_dataset["debug_render_time_gap"] = mRenderer.debug_render_time_gap
        # endregion

        # region 初始化及计算数值
        # region 创建文件夹
        dataset_root = os.path.join(pm.curr_project.get_info('output_root'), "dataset")
        raw_image_root = os.path.join(dataset_root, "raw_image")
        mask_image_root = os.path.join(dataset_root, "mask_image")
        if not os.path.exists(raw_image_root):
            os.makedirs(raw_image_root)
        if not os.path.exists(mask_image_root):
            os.makedirs(mask_image_root)
        pix2pix_dataset_root = os.path.join(dataset_root, "pix2pix_dataset")
        pix2pix_train_a_root = os.path.join(pix2pix_dataset_root, "train_A")
        pix2pix_train_b_root = os.path.join(pix2pix_dataset_root, "train_B")
        if opt["enable_pix2pix_output"]:
            if not os.path.exists(pix2pix_train_a_root):
                os.makedirs(pix2pix_train_a_root)
            if not os.path.exists(pix2pix_train_b_root):
                os.makedirs(pix2pix_train_b_root)
        # endregion
        raw_image_idx = 0
        mask_image_idx = 0
        pix2pix_image_idx = 0
        # 禁用_imgui_preview_boundary_bbox和_imgui_preview_ground_cube
        cls._imgui_preview_boundary_bbox = False
        cls._imgui_preview_ground_cube = False

        from gui.graphic.geometry import SimpleCube, WiredBoundingBox
        bbox: "WiredBoundingBox" = cls._mask_boundary_debug_bbox
        cls._tmp_geo_as_mask = mRenderer.geometry_collection.add_geometry(SimpleCube("_random_mask_geo"))

        mRenderer.update_size(512, 512)
        mRenderer.debug_render_time_gap = 0  # instant render mode
        yield None  # need yield to ensure renderer settings applied
        # endregion

        # region 生成n个mask
        for i in range(opt["num_masks"]):
            print(f"========== mask_{i} ==========")
            # region move mask bbox
            center_x = random.uniform(bbox.bound_min[0], bbox.bound_max[0])
            center_y = random.uniform(bbox.bound_min[1], bbox.bound_max[1])
            center_z = cls._ground_height
            camera_target = (center_x, -center_z, center_y)
            aspect_ratio = 99999
            size_x = opt["mask_size_min"]
            size_y = opt["mask_size_min"]
            size_z = 10
            while aspect_ratio > 3:
                size_x = random.uniform(opt["mask_size_min"], opt["mask_size_max"])
                size_y = random.uniform(opt["mask_size_min"], opt["mask_size_max"])
                aspect_ratio = max(size_x, size_y) / min(size_x, size_y)
            cls._tmp_geo_as_mask.translation = (center_x, center_y, center_z)
            cls._tmp_geo_as_mask.scale = (size_x, size_y, size_z)
            # endregion

            # region render raw gaussian
            mRenderer.render_gaussians = True
            mRenderer.render_geometries = False
            mRenderer.render_debug_geometries = False
            yield None

            print("开始创建原始高斯图像")
            coroutine = cls.camera_orbit_coroutine(camera_target)
            raw_image_arrs = []
            while True:
                try:
                    radius, angle_x, angle_y = next(coroutine)
                    yield None
                    file_path = os.path.join(raw_image_root, f'{raw_image_idx:05d}.jpg')
                    raw_arr = mRenderer.frame_to_arr()[:, :, :3]
                    raw_image = Image.fromarray(raw_arr)
                    raw_image.save(file_path, quality=90)
                    raw_image_arrs.append(raw_arr)
                    raw_image_idx += 1
                except StopIteration:
                    break
                except Exception as e:
                    print(e)
            # endregion

            # region render masks
            for gm in mRenderer.gaussian_collection.gaussian_managers:
                mask_wrapper = GaussianMaskWrapper(f"mask_{i}", gm, cls._tmp_geo_as_mask)
                success, msg = mask_wrapper.create_mask_by_parent()
                if not success:
                    print(msg)
                    continue
                mask = mask_wrapper.mask
                gm.cache()
                gm.paint_by_mask(mask)
            mRenderer.render_gaussians = True
            mRenderer.render_geometries = False
            mRenderer.render_debug_geometries = False
            yield None
            print("开始创建蒙版图像")
            coroutine = cls.camera_orbit_coroutine(camera_target)
            mask_image_arrs = []
            while True:
                try:
                    radius, angle_x, angle_y = next(coroutine)
                    yield None
                    file_path = os.path.join(mask_image_root, f'{mask_image_idx:05d}.jpg')
                    mask_arr = mRenderer.frame_to_arr()[:, :, :3]
                    mask_image = Image.fromarray(mask_arr)
                    mask_image.save(file_path, quality=90)
                    mask_image_arrs.append(mask_arr)
                    mask_image_idx += 1
                except StopIteration:
                    break
                except Exception as e:
                    print(e)
            for gm in mRenderer.gaussian_collection.gaussian_managers:
                gm.restore()
            # endregion

            # create pix2pix datasets
            if opt["enable_pix2pix_output"]:

                assert len(raw_image_arrs) == len(mask_image_arrs)
                pink_color = np.array([255, 0, 255])  # 粉色的 RGB 值

                for j in range(len(raw_image_arrs)):
                    raw_arr = raw_image_arrs[j]
                    mask_arr = mask_image_arrs[j]
                    brightness = mask_arr[:, :, 0]  # 0 - 255
                    white_pixels = brightness > 128
                    image_a_arr = raw_arr.copy()
                    image_a_arr[white_pixels] = pink_color
                    image_a = Image.fromarray(image_a_arr)
                    image_b = Image.fromarray(raw_arr)

                    train_a_path = os.path.join(pix2pix_train_a_root, f'{pix2pix_image_idx:05d}.jpg')
                    train_b_path = os.path.join(pix2pix_train_b_root, f'{pix2pix_image_idx:05d}.jpg')

                    image_a.save(train_a_path, quality=90)
                    image_b.save(train_b_path, quality=90)

                    pix2pix_image_idx += 1
            # endregion

            if cls._imgui_create_dataset_stop_signal:
                print("检测到终止信号")
                raise StopIteration

            yield None
        # endregion

    @classmethod
    def on_create_dataset_stop(cls):
        mRenderer = cls.ViewerContentClass.mRenderer

        cls._imgui_create_dataset_stop_signal = False
        if cls._tmp_geo_as_mask is not None:
            cls.ViewerContentClass.mRenderer.geometry_collection.remove_geometry(cls._tmp_geo_as_mask)

        # 恢复初始值
        cls._imgui_preview_ground_cube = cls._parameters_before_create_dataset["preview_ground_cube"]
        cls._imgui_preview_boundary_bbox = cls._parameters_before_create_dataset["preview_boundary_bbox"]
        mRenderer.render_debug_geometries = cls._parameters_before_create_dataset["raw_enable_render_debug_geometries"]
        mRenderer.render_geometries = cls._parameters_before_create_dataset["raw_enable_render_geometries"]
        mRenderer.render_gaussians = cls._parameters_before_create_dataset["raw_enable_render_gaussians"]
        mRenderer.update_size(cls._parameters_before_create_dataset["image_width"],
                              cls._parameters_before_create_dataset["image_height"])
        mRenderer.debug_render_time_gap = cls._parameters_before_create_dataset["debug_render_time_gap"]

    @classmethod
    def camera_orbit_coroutine(cls, target):
        mRenderer = cls.ViewerContentClass.mRenderer
        opt = cls._dataset_creation_settings
        radius_samples = np.linspace(opt["camera_radius_min"], opt["camera_radius_max"], opt["radius_sample"])
        angle_y_samples = np.linspace(opt["camera_angle_y_min"], opt["camera_angle_y_max"], opt["angle_y_sample"])
        angle_x_samples = np.linspace(0, 360 - 360 / opt["angle_x_sample"], opt["angle_x_sample"])
        for radius in radius_samples:
            for angle_y in angle_y_samples:
                for angle_x in angle_x_samples:
                    print(f'r={radius}, a_x={angle_x}, a_y={angle_y}')
                    mRenderer.camera.target = target
                    mRenderer.camera.radius = radius
                    mRenderer.camera.angle_x = angle_x
                    mRenderer.camera.angle_y = angle_y
                    mRenderer.camera.update()
                    yield radius, angle_x, angle_y

    # endregion

    @classmethod
    def on_project_changed(cls):
        print("on project changed in full page")
        cls._mask_boundary_debug_bbox = None
        cls._mask_ground_debug_cube = None
        if pm.curr_project is not None:
            print("settings")
            cls._dataset_creation_settings = pm.curr_project.get_project_data(pd.DATASET_CREATION_SETTINGS, {})
            print(cls._dataset_creation_settings)
            if len(cls._dataset_creation_settings) == 0:
                cls._dataset_creation_settings = cls._dataset_creation_settings_default
                pm.curr_project.set_project_data(pd.DATASET_CREATION_SETTINGS, cls._dataset_creation_settings)


EventModule.register_project_change_callback(FullPage.on_project_changed)


class GaussianMaskWrapper:
    """
    包裹了一个mask， 实现更高级的功能
    """

    def __init__(self, name, parent_gaussian_manager, parent_geometry):
        self.name = name
        self.parent_gaussian_manager = parent_gaussian_manager
        self.parent_geometry = parent_geometry

        self.mask = None
        self.num_points = 0

    def create_mask_by_parent(self) -> tuple[bool, str]:
        if self.parent_gaussian_manager is None:
            return False, "no target gaussian manager"
        if self.parent_geometry is None:
            return False, "no target geometry as mask"

        self.mask = self.parent_geometry.is_points_inside(self.parent_gaussian_manager.gaussians.get_xyz)
        if self.mask is None:
            return False, f"target_geometry_as_mask {self.parent_geometry.name} does not support " \
                          f"get points inside function"

        self.num_points = self.mask.sum().item()
        return True, "Success"

    def assign_mask(self, mask):
        self.mask = mask
        self.num_points = self.mask.sum().item()
        self.parent_geometry = None
        self.parent_gaussian_manager = None

    def has_parent(self):
        return self.parent_geometry is not None and self.parent_gaussian_manager is not None
