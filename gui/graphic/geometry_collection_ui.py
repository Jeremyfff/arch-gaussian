# -*- coding: utf-8 -*-
# @Author  : Yiheng Feng
# @Time    : 12/9/2024 6:50 PM
# @Function:

import imgui
import numpy as np

from gui.components import c
from gui.global_app_state import g
from gui.utils import name_utils
from gui.graphic import geometry

__runtime__ = True
if not __runtime__:
    from gui.graphic.geometry_collection import GaussianCollection, EditableGeometryCollection, PointCloudCollection


class GaussianCollectionUI:
    def __init__(self, host: "GaussianCollection"):
        self.host = host

        self._imgui_curr_selected_geo_idx = -1

        from gui.windows import GaussianInspectorWindow
        self.InspectorWindow = GaussianInspectorWindow
        self.InspectorWindow.register_w_close_event(self._clear_imgui_curr_selected_geo_idx)

    def operation_panel(self):
        self._operation_panel_buttons_region()
        imgui.separator()
        self._operation_panel_list_region()

    def show_debug_info(self):
        c.bold_text(f'[{self.host.__class__.__name__}]')
        imgui.same_line()
        imgui.text(f'final_gm: {self.host.final_gm is not None}')
        imgui.same_line()
        if imgui.button('show operation_panel'):
            imgui.open_popup('op_panel')
        if imgui.begin_popup('op_panel'):
            self.operation_panel()
            imgui.end_popup()

    def _operation_panel_buttons_region(self):
        # region ADD BUTTON ===============================================================
        gm = c.load_gaussian_from_custom_file_button(uid="load_gaussian_from_custom_file_button_in_gaussian_collection")
        if gm is not None:
            self.host.add_gaussian_manager(gm)
            self.host.merge_gaussians()
        imgui.same_line()
        gm = c.load_gaussian_from_iteration_button(uid="load_gaussian_from_iteration_button_in_gaussian_collection")
        if gm is not None:
            self.host.add_gaussian_manager(gm)
            self.host.merge_gaussians()
        # endregion =======================================================================

        # region MERGE BUTTON =============================================================
        if c.icon_text_button('stack-fill', 'Merge Gaussian'):
            self.host.merge_gaussians()
        c.easy_tooltip('Merge Gaussian Manually')
        # endregion =======================================================================

    def _operation_panel_list_region(self):
        # region GAUSSIANS LIST ===========================================================
        # GUI -----------------------------------------------------------------------------
        imgui.text('GAUSSIANS LIST')
        c.begin_child(f'{self.host.name}_child', 0, 100 * g.global_scale, border=True)
        _only_have_one_gm = len(self.host.gaussian_managers) == 1
        for i, gm in enumerate(self.host.gaussian_managers):
            _selected = (i == self._imgui_curr_selected_geo_idx)
            opened, _selected = imgui.selectable(f"[{i}]{gm.source_ply_path}", _selected)
            if opened and _selected:
                self._imgui_curr_selected_geo_idx = i
                self.InspectorWindow.register_content(None)  # TODO
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
            self.host.remove_geometry(self.host.gaussian_managers[self._imgui_curr_selected_geo_idx])
            self.InspectorWindow.w_close()
        # merge
        if changed:
            self.host.merge_gaussians()
        # END LOGICS ----------------------------------------------------------------------
        # endregion =======================================================================

    def _clear_imgui_curr_selected_geo_idx(self):
        self._imgui_curr_selected_geo_idx = -1


class EditableGeometryCollectionUI:
    def __init__(self, host: "EditableGeometryCollection"):
        self.host = host

        from gui.windows import GeometryInspectorWindow
        self.InspectorWindow = GeometryInspectorWindow
        self.InspectorWindow.register_w_close_event(self._clear_imgui_curr_selected_geo_idx)

        self._imgui_curr_selected_geo_idx = -1

    def _clear_imgui_curr_selected_geo_idx(self):
        self._imgui_curr_selected_geo_idx = -1

    def operation_panel(self):
        changed = False
        # region ADD BUTTON ===============================================================
        if c.icon_text_button('file-add-fill', 'Add Geo', uid="MCGCOP_Add_Geo"):
            imgui.open_popup("MCGCOP_add_geo_popup")
        if imgui.begin_popup("MCGCOP_add_geo_popup"):
            if imgui.menu_item("add cube simple")[0]:
                all_cube_names = [geo.name for geo in self.host.geometries if geo.name.startswith('cube')]
                geo_name = f"cube_{name_utils.get_next_name_idx(all_cube_names)}"
                self.host.add_geometry(geometry.SimpleCube(geo_name))
            if imgui.menu_item("add wired box")[0]:
                all_wired_box_names = [geo.name for geo in self.host.geometries if geo.name.startswith('wired_box')]
                geo_name = f"wired_box_{name_utils.get_next_name_idx(all_wired_box_names)}"
                self.host.add_geometry(geometry.WiredBoundingBox(geo_name, (-1, -1, -1), (1, 1, 1)))
            if imgui.menu_item("add polygon 3d")[0]:
                all_polygon_names = [geo.name for geo in self.host.geometries if geo.name.startswith('polygon3d')]
                geo_name = f"polygon3d_{name_utils.get_next_name_idx(all_polygon_names)}"
                self.host.add_geometry(
                    geometry.Polygon3D(geo_name,
                                       np.array([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]),
                                       -10, 10))
            if imgui.menu_item("add polygon 2d")[0]:
                all_polygon_names = [geo.name for geo in self.host.geometries if geo.name.startswith('polygon2d')]
                geo_name = f"polygon2d_{name_utils.get_next_name_idx(all_polygon_names)}"
                self.host.add_geometry(
                    geometry.Polygon(geo_name,
                                     np.array([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)])))
            imgui.end_popup()
        # endregion =======================================================================
        # region other buttons
        imgui.same_line()
        if c.icon_text_button('file-add-fill', 'More...', uid="MCGCOP_More"):
            imgui.open_popup("MCGCOP_more_popup")
        if imgui.begin_popup("MCGCOP_more_popup"):
            imgui.checkbox("test check box", True)
            imgui.end_popup()

        # endregion

        # region GEO LIST ===========================================================
        # GUI -----------------------------------------------------------------------------
        imgui.text('GEOMETRY LIST')
        c.begin_child(f'{self.host.name}_child', 0, 200 * g.global_scale, border=True)

        for i, geo in enumerate(self.host.geometries):
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
            self.host.remove_geometry(self.host.geometries[self._imgui_curr_selected_geo_idx])
            self.InspectorWindow.w_close()
        # END LOGICS ----------------------------------------------------------------------
        # endregion =======================================================================

    def show_debug_info(self):
        pass


class PointCloudCollectionUI:
    def __init__(self, host: "PointCloudCollection"):
        self.host = host

    def operation_panel(self):
        imgui.text(f'Point Cloud Collection with [{self.host.num_points}] points')
        changed, delete_self = self.host.point_cloud.operation_panel()
        if delete_self:
            self.host.delete_self()

    def show_debug_info(self):
        c.bold_text(f'[{self.host.__class__.__name__}]')
        imgui.same_line()
        imgui.text(f'num_points: {self.host.num_points}')

