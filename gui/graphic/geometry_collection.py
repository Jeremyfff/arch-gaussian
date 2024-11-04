import uuid
from abc import abstractmethod
from typing import Union, Optional

import imgui
import numpy as np

from gui import components as c
from gui import global_var as g
from gui.graphic import geometry
from gui.graphic.geometry import BaseGeometry, BaseGeometry3D
from gui.modules import EventModule
from gui.utils import name_utils

SUPPORTED_GEO_TYPES = Union[BaseGeometry, BaseGeometry3D]


class GeometryCollection:

    def __init__(self, name, camera):
        self.name = name
        self.camera = camera
        self.geometries: list[SUPPORTED_GEO_TYPES] = []

    def add_geometry(self, geo):
        self.geometries.append(geo)
        return geo

    def add_geometries(self, *geometries):
        for geo in geometries:
            self.add_geometry(geo)
        return geometries

    def clear(self):
        self.geometries.clear()

    def remove_geometry(self, geo):
        if geo is None:
            return
        if geo not in self.geometries:
            return
        self.geometries.remove(geo)
        return geo

    def render(self):
        for geo in self.geometries:
            if geo.active:
                geo.render(self.camera)

    @abstractmethod
    def operation_panel(self):
        pass

    @abstractmethod
    def show_debug_info(self):
        pass


class PointCloudCollection(GeometryCollection):

    def __init__(self, name, camera, pos_arr=None, color_arr=None):
        super().__init__(name, camera)

        if pos_arr is None or color_arr is None:
            num = 100
            pos_arr = np.random.rand(num, 3).astype(np.float32)
            color_arr = np.random.rand(num, 4).astype(np.float32)

        self._debug_num_points = -1
        self.point_cloud: Optional[geometry.PointCloud] = None

        self.set_points_cloud(pos_arr, color_arr)
        self.axis3d = self.add_geometry(geometry.Axis3D())

    def set_points_cloud(self, pos_arr, color_arr):
        pos_arr = pos_arr.astype(np.float32)
        color_arr = color_arr.astype(np.float32)
        self.remove_geometry(self.point_cloud)
        self.point_cloud = self.add_geometry(geometry.PointCloud('point_cloud', pos_arr, color_arr))
        self._debug_num_points = len(pos_arr)

    def operation_panel(self):
        imgui.text('nothing to show for PointCloudCollection')

    def show_debug_info(self):
        c.bold_text(f'[{self.__class__.__name__}]')
        imgui.same_line()
        imgui.text(f'num_points: {self._debug_num_points}')


class GaussianCollection(GeometryCollection):
    def __init__(self, name, camera, debug_collection=None):
        """
        GaussianPointCloud的集合

        可以附带指定一个debug_collection， 用于显示debug图形信息
        """
        super().__init__(name, camera)

        import torch
        self.torch = torch
        from gui.windows import GaussianInspectorWindow
        self.InspectorWindow = GaussianInspectorWindow
        from src.manager.gaussian_manager import GaussianManager

        self.final_gm: Optional[GaussianManager] = None
        """当Collection中有多个GaussianPointCloud时， 合并后的最终GaussianPointCloud"""

        self.InspectorWindow.register_w_close_event(self._clear_imgui_curr_selected_geo_idx)

        self.geometries: list[geometry.GaussianPointCloud] = []  # 指定类型用
        self.debug_collection: Optional[DebugCollection] = debug_collection

        self._imgui_curr_selected_geo_idx = -1
        EventModule.register_get_depth_callback(self.on_get_depth)

    def set_gaussian_manager(self, gm):
        """
        清空场景中的所有geometries(Gaussian Point Cloud)，
        并由该gm(Gaussian Manager)创建一个新的Gaussian Point Cloud， 添加到场景中。

        如果gm为None， 则清空场景的geometries

        该方法由上层的GaussianRenderer.set_gaussian_manager(gm)调用
        """
        self.geometries = []
        if gm is not None:
            self.add_gaussian_manager(gm)
        self.merge_gaussians()

    def add_gaussian_manager(self, gm):
        """向场景中添加一个新的Gaussian Point Cloud， 其包裹传入的gm(Gaussian Manager)"""
        if gm is None:
            return
        name = name_utils.ply_path_to_model_name(gm.source_ply_path)
        if name == '':
            name_idx = name_utils.get_next_name_idx([geo.name for geo in self.geometries])
            name = f"gaussian_{name_idx}"
        else:
            name_idx = name_utils.get_next_name_idx([geo.name for geo in self.geometries if geo.name.startswith(name)])
            name = f"{name}_{name_idx}" if name_idx > 0 else name
        gs_pt_cloud = geometry.GaussianPointCloud(
            name=name, gaussian_manager=gm, debug_collection=self.debug_collection
        )
        gs_pt_cloud.generate_gaussian_points()
        self.add_geometry(gs_pt_cloud)
        return gs_pt_cloud

    def merge_gaussians(self):
        from src.manager.gaussian_manager import GaussianManager
        self.final_gm = GaussianManager.merge_gaussian_managers([geo.gm for geo in self.geometries])

    def render_gaussian(self) -> Optional[np.ndarray]:
        """使用3dgs提供的接口渲染画面， 返回图像array"""
        if self.final_gm is None:
            return None
        return self.final_gm.render(self.camera, convert_to_rgba_arr=True)

    def render(self):
        """常规渲染方法，使用opengl渲染点云（主要用作深度测试）"""
        super().render()

    def on_get_depth(self, *args, **kwargs):
        _ = self
        pass

    def _clear_imgui_curr_selected_geo_idx(self):
        self._imgui_curr_selected_geo_idx = -1

    def operation_panel(self):
        self._operation_panel_buttons_region()
        imgui.separator()
        self._operation_panel_list_region()

    def _operation_panel_buttons_region(self):
        # region ADD BUTTON ===============================================================
        gm = c.load_gaussian_from_custom_file_button(uid="load_gaussian_from_custom_file_button_in_gaussian_collection")
        if gm is not None:
            self.add_gaussian_manager(gm)
            self.merge_gaussians()
        imgui.same_line()
        gm = c.load_gaussian_from_iteration_button(uid="load_gaussian_from_iteration_button_in_gaussian_collection")
        if gm is not None:
            self.add_gaussian_manager(gm)
            self.merge_gaussians()
        # endregion =======================================================================

        # region MERGE BUTTON =============================================================
        if c.icon_text_button('stack-fill', 'Merge Gaussian'):
            self.merge_gaussians()
        c.easy_tooltip('Merge Gaussian Manually')
        # endregion =======================================================================

    def _operation_panel_list_region(self):
        # region GAUSSIANS LIST ===========================================================
        # GUI -----------------------------------------------------------------------------
        imgui.text('GAUSSIANS LIST')
        c.begin_child(f'{self.name}_child', 0, 100 * g.GLOBAL_SCALE, border=True)
        only_have_one_geo = len(self.geometries) == 1
        for i, gs_pt_cloud in enumerate(self.geometries):
            selected = i == self._imgui_curr_selected_geo_idx
            opened, selected = imgui.selectable(gs_pt_cloud.name, selected)
            if opened and selected:
                print(f'opened and selected {i}')
                self._imgui_curr_selected_geo_idx = i
                self.InspectorWindow.register_content(gs_pt_cloud.operation_panel, is_the_only_geo=only_have_one_geo)
        # 取消选择
        if imgui.is_mouse_clicked(0) and imgui.is_window_hovered() and not imgui.is_any_item_hovered():
            self._clear_imgui_curr_selected_geo_idx()
            self.InspectorWindow.unregister_content()
        imgui.end_child()
        # END GUI -------------------------------------------------------------------------
        # LOGICS --------------------------------------------------------------------------
        results = self.InspectorWindow.get_results()
        if results:
            changed, delete_self = results
        else:
            changed, delete_self = False, False
        # delete
        if delete_self:
            self.remove_geometry(self.geometries[self._imgui_curr_selected_geo_idx])
            self.InspectorWindow.w_close()
        # merge
        if changed:
            self.merge_gaussians()
        # END LOGICS ----------------------------------------------------------------------
        # endregion =======================================================================

    def show_debug_info(self):
        c.bold_text(f'[{self.__class__.__name__}]')
        imgui.same_line()
        imgui.text(f'final_gm: {self.final_gm is not None}')
        imgui.same_line()
        if imgui.button('show operation_panel'):
            imgui.open_popup('op_panel')
        if imgui.begin_popup('op_panel'):
            self.operation_panel()
            imgui.end_popup()


class DebugCollection(GeometryCollection):
    """用于显示各种debug物体, 这是一种特殊的collection， 其物体每帧刷新"""

    def __init__(self, name, camera):
        super().__init__(name, camera)

    def draw_bbox(self, bbox, skip_examine=False):
        if not skip_examine:
            if bbox in self.geometries:
                return

        self.geometries.append(bbox)

    def draw_cube(self, cube, skip_examine=False):
        if not skip_examine:
            if cube in self.geometries:
                return
        self.geometries.append(cube)

    def draw_geo(self, geo, skip_examine=False):
        if not skip_examine:
            if geo in self.geometries:
                return
        self.geometries.append(geo)

    def render(self):
        super().render()
        self.geometries.clear()

    def operation_panel(self):
        pass

    def show_debug_info(self):
        pass


class MyCustomGeometryCollection(GeometryCollection):
    def __init__(self, name, camera):
        super().__init__(name, camera)
        from gui.windows import GeometryInspectorWindow
        self.InspectorWindow = GeometryInspectorWindow
        self.InspectorWindow.register_w_close_event(self._clear_imgui_curr_selected_geo_idx)

        self._imgui_curr_selected_geo_idx = -1

    def _clear_imgui_curr_selected_geo_idx(self):
        self._imgui_curr_selected_geo_idx = -1

    def operation_panel(self):
        changed = False
        c.bold_text(f'[GEOMETRY COLLECTION SETTINGS]')
        # region ADD BUTTON ===============================================================
        if c.icon_text_button('file-add-fill', 'Add Geo', uid="MCGCOP_Add_Geo"):
            imgui.open_popup("MCGCOP_add_geo_popup")
        if imgui.begin_popup("MCGCOP_add_geo_popup"):
            if imgui.menu_item("add cube simple")[0]:
                all_cube_names = [geo.name for geo in self.geometries if geo.name.startswith('cube')]
                geo_name = f"cube_{name_utils.get_next_name_idx(all_cube_names)}"
                self.add_geometry(geometry.SimpleCube(geo_name))
            if imgui.menu_item("add wired box")[0]:
                all_wired_box_names = [geo.name for geo in self.geometries if geo.name.startswith('wired_box')]
                geo_name = f"wired_box_{name_utils.get_next_name_idx(all_wired_box_names)}"
                self.add_geometry(geometry.WiredBoundingBox(geo_name, (-1, -1, -1), (1, 1, 1)))
            if imgui.menu_item("add polygon 3d")[0]:
                all_polygon_names = [geo.name for geo in self.geometries if geo.name.startswith('polygon3d')]
                geo_name = f"polygon3d_{name_utils.get_next_name_idx(all_polygon_names)}"
                self.add_geometry(
                    geometry.Polygon3D(geo_name,
                                       np.array([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]),
                                       -10, 10))
            if imgui.menu_item("add polygon 2d")[0]:
                all_polygon_names = [geo.name for geo in self.geometries if geo.name.startswith('polygon2d')]
                geo_name = f"polygon2d_{name_utils.get_next_name_idx(all_polygon_names)}"
                self.add_geometry(
                    geometry.Polygon(geo_name,
                                       np.array([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)])))
            imgui.end_popup()
        # endregion =======================================================================
        # region other buttons
        imgui.same_line()
        if c.icon_text_button('file-add-fill', 'More...', uid="MCGCOP_Add_Geo"):
            imgui.open_popup("MCGCOP_more_popup")
        if imgui.begin_popup("MCGCOP_more_popup"):
            imgui.checkbox("test check box", True)
            imgui.end_popup()

        # endregion

        # region GEO LIST ===========================================================
        # GUI -----------------------------------------------------------------------------
        imgui.text('GEOMETRY LIST')
        c.begin_child(f'{self.name}_child', 0, 200 * g.GLOBAL_SCALE, border=True)

        for i, geo in enumerate(self.geometries):
            selected = i == self._imgui_curr_selected_geo_idx
            opened, selected = imgui.selectable(geo.name, selected)
            if opened and selected:
                self._imgui_curr_selected_geo_idx = i
                self.InspectorWindow.register_content(geo.operation_panel)
        # 取消选择
        if imgui.is_mouse_clicked(0) and imgui.is_window_hovered() and not imgui.is_any_item_hovered():
            self._clear_imgui_curr_selected_geo_idx()
            self.InspectorWindow.unregister_content()
        imgui.end_child()
        # END GUI -------------------------------------------------------------------------
        # LOGICS --------------------------------------------------------------------------
        results = self.InspectorWindow.get_results()
        if results:
            changed, delete_self = results
        else:
            changed = False
            delete_self = False
        # delete
        if delete_self:
            self.remove_geometry(self.geometries[self._imgui_curr_selected_geo_idx])
            self.InspectorWindow.w_close()
        # END LOGICS ----------------------------------------------------------------------
        # endregion =======================================================================

    def show_debug_info(self):
        pass
