import copy
import logging
import uuid
from abc import abstractmethod
from typing import Union, Optional

import imgui
import numpy as np

from gui import components as c
from gui import global_var as g
from gui.graphic import geometry
from gui.graphic.geometry import BaseGeometry, BaseGeometry3D

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
    def __init__(self, name, camera):
        super().__init__(name, camera)
        from src.manager.gaussian_manager import GaussianManager
        self.final_gm: Optional[GaussianManager] = None
        import torch
        self.torch = torch

        self.geometries: list[geometry.GaussianPointCloud] = []  # 指定类型用
        self._geometries_to_delete = set()  # 将要被删除的geo

    def set_gaussian_manager(self, gm):
        """兼容GaussianPointCloud, 一般在一个gm的时候使用
        如果gm为None， 则清空场景的geometries"""
        self.geometries = []
        if gm is not None:
            self.add_gaussian_manager(gm)
        self.merge_gaussian()

    def add_gaussian_manager(self, gm, name=None):
        if gm is None:
            return
        if name is None:
            name = str(uuid.uuid4())
        gs_pt_cloud = geometry.GaussianPointCloud(name)
        gs_pt_cloud.set_gaussian_manager(gm)
        gs_pt_cloud.update_gaussian_points()
        self.add_geometry(gs_pt_cloud)
        return gs_pt_cloud

    def add_gaussian_from_file(self, file_path=None):
        if file_path is None:
            from gui.utils.io_utils import open_file_dialog
            file_path = open_file_dialog()
        if file_path == '':
            return
        from src.manager.gaussian_manager import GaussianManager
        from gui.contents.pages.train_3dgs_pages import FullTrainingPage
        args = FullTrainingPage.gen_config_args()
        try:
            self.add_gaussian_manager(GaussianManager(args, None, file_path))
        except Exception as e:
            logging.error(e)

    def merge_gaussian(self):
        if len(self.geometries) == 0:
            logging.warning('no gaussian pt cloud in this collection')
            self.final_gm = None
            return
        if len(self.geometries) == 1:
            self.final_gm = self.geometries[0].gm
            return
        logging.info('merging gaussian')
        with self.torch.no_grad():
            self.final_gm = copy.deepcopy(self.geometries[0].gm)
            final_xyz_list = []
            final_features_dc_list = []
            final_features_rest_list = []
            final_scaling_list = []
            final_rotation_list = []
            final_opacity_list = []
            final_max_radii2D_list = []
            for i, gs_pt_cloud in enumerate(self.geometries):
                gaussians = gs_pt_cloud.gm.gaussians
                final_xyz_list.append(gaussians._xyz.detach())
                final_features_dc_list.append(gaussians._features_dc.detach())
                final_features_rest_list.append(gaussians._features_rest.detach())
                final_scaling_list.append(gaussians._scaling.detach())
                final_rotation_list.append(gaussians._rotation.detach())
                final_opacity_list.append(gaussians._opacity.detach())
                final_max_radii2D_list.append(gaussians.max_radii2D.detach())

            self.final_gm.gaussians._xyz = self.torch.cat(final_xyz_list, dim=0)
            self.final_gm.gaussians._features_dc = self.torch.cat(final_features_dc_list, dim=0)
            self.final_gm.gaussians._features_rest = self.torch.cat(final_features_rest_list, dim=0)
            self.final_gm.gaussians._scaling = self.torch.cat(final_scaling_list, dim=0)
            self.final_gm.gaussians._rotation = self.torch.cat(final_rotation_list, dim=0)
            self.final_gm.gaussians._opacity = self.torch.cat(final_opacity_list, dim=0)
            self.final_gm.gaussians.max_radii2D = self.torch.cat(final_max_radii2D_list, dim=0)

    def render_gaussian(self) -> Optional[np.ndarray]:
        if self.final_gm is None:
            return None
        return self.final_gm.render(self.camera, convert_to_rgba_arr=True)

    def render(self):
        super().render()

    def operation_panel(self):
        changed = False
        c.bold_text(f'[{self.__class__.__name__}]')
        if c.icon_text_button('file-add-fill', 'Add Gaussian'):
            self.add_gaussian_from_file()
            changed |= True
        c.easy_tooltip('Add Gaussian From Ply file')
        imgui.same_line()
        if c.icon_text_button('stack-fill', 'Merge Gaussian'):
            self.merge_gaussian()
        c.easy_tooltip('Merge Gaussian Manually')
        imgui.separator()
        imgui.text('GAUSSIANS')
        c.begin_child(f'{self.name}_child', 0, 200 * g.GLOBAL_SCALE, border=True)
        self._geometries_to_delete.clear()  # 清空删除列表
        for gs_pt_cloud in self.geometries:
            if imgui.begin_menu(gs_pt_cloud.name).opened:
                changed, delete_self = gs_pt_cloud.operation_panel()
                if delete_self:
                    # 加入删除列表
                    self._geometries_to_delete.add(gs_pt_cloud)
                imgui.end_menu()
        imgui.end_child()
        # 删除逻辑
        for gs_pt_cloud in self._geometries_to_delete:
            self.remove_geometry(gs_pt_cloud)
        # merge
        if changed:
            self.merge_gaussian()

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
        # imgui.indent()
        # for ps_pt_cloud in self.geometries:
        #     ps_pt_cloud.show_debug_info()
        # imgui.unindent()
