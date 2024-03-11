import copy
import logging
from abc import abstractmethod
from typing import Union, Optional

import imgui
import numpy as np

from gui import components as c
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
        pass

    def show_debug_info(self):
        c.bold_text(f'[{self.__class__.__name__}]')
        imgui.same_line()
        imgui.text(f'num_points: {self._debug_num_points}')


class GaussianCollection(GeometryCollection):
    def __init__(self, name, camera):
        super().__init__(name, camera)
        from src.manager.gaussian_manager import GaussianManager
        self.final_gm: Optional[GaussianManager] = None
        self.gs_pt_cloud_list: list[geometry.GaussianPointCloud] = []
        import torch
        self.torch = torch

    def set_gaussian_manager(self, gm):
        """兼容GaussianPointCloud, 一般在一个gm的时候使用"""
        gs_pt_cloud = geometry.GaussianPointCloud('gaussian_point_cloud')
        gs_pt_cloud.set_gaussian_manager(gm)
        gs_pt_cloud.update_gaussian_points()
        self.gs_pt_cloud_list = [gs_pt_cloud]

    def update_gaussian_points(self):
        for gs_pt_cloud in self.gs_pt_cloud_list:
            gs_pt_cloud.update_gaussian_points()

    def add_gaussian_manager(self, name, gm):
        gs_pt_cloud = geometry.GaussianPointCloud(name)
        gs_pt_cloud.set_gaussian_manager(gm)
        gs_pt_cloud.update_gaussian_points()
        self.gs_pt_cloud_list.append(gs_pt_cloud)
        return gs_pt_cloud

    def merge_gaussian(self):
        if len(self.gs_pt_cloud_list) == 0:
            logging.warning('no gaussian pt cloud in this collection')
            return
        if len(self.gs_pt_cloud_list) == 1:
            self.final_gm = self.gs_pt_cloud_list[0].gm
            return
        with self.torch.no_grad():
            self.final_gm = copy.deepcopy(self.gs_pt_cloud_list[0].gm)
            final_xyz_list = []
            final_features_dc_list = []
            final_features_rest_list = []
            final_scaling_list = []
            final_rotation_list = []
            final_opacity_list = []
            final_max_radii2D_list = []
            final_xyz_gradient_accum_list = []
            final_denom_list = []
            for i, gs_pt_cloud in enumerate(self.gs_pt_cloud_list):
                gaussians = gs_pt_cloud.gm.gaussians
                final_xyz_list.append(gaussians._xyz.detach())
                final_features_dc_list.append(gaussians._features_dc.detach())
                final_features_rest_list.append(gaussians._features_rest.detach())
                final_scaling_list.append(gaussians._scaling.detach())
                final_rotation_list.append(gaussians._rotation.detach())
                final_opacity_list.append(gaussians._opacity.detach())
                final_max_radii2D_list.append(gaussians._max_radii2D.detach())
                final_xyz_gradient_accum_list.append(gaussians._xyz_gradient_accum.detach())
                final_denom_list.append(gaussians._denom.detach())

            self.final_gm.gaussians._xyz = self.torch.cat(final_xyz_list, dim=0)
            self.final_gm.gaussians._features_dc = self.torch.cat(final_features_dc_list, dim=0)
            self.final_gm.gaussians._features_rest = self.torch.cat(final_features_rest_list, dim=0)
            self.final_gm.gaussians._scaling = self.torch.cat(final_scaling_list, dim=0)
            self.final_gm.gaussians._rotation = self.torch.cat(final_rotation_list, dim=0)
            self.final_gm.gaussians._opacity = self.torch.cat(final_opacity_list, dim=0)
            self.final_gm.gaussians._max_radii2D = self.torch.cat(final_max_radii2D_list, dim=0)
            self.final_gm.gaussians._xyz_gradient_accum = self.torch.cat(final_xyz_gradient_accum_list, dim=0)
            self.final_gm.gaussians._denom = self.torch.cat(final_denom_list, dim=0)

    def render(self):
        assert self.final_gm is not None
        return self.final_gm.render(self.camera, convert_to_rgba_arr=True)

    def operation_panel(self):
        imgui.button('add gaussian manager')
        imgui.button('delete gaussian manager')
        if imgui.button('merge_gaussian'):
            self.merge_gaussian()
        for ps_pt_cloud in self.gs_pt_cloud_list:
            c.bold_text(ps_pt_cloud.name)
            ps_pt_cloud.operation_panel()
            imgui.separator()

    def show_debug_info(self):
        c.bold_text(f'[{self.__class__.__name__}]')
        if imgui.button('show operation_panel'):
            imgui.open_popup('op_panel')
        for ps_pt_cloud in self.gs_pt_cloud_list:
            ps_pt_cloud.show_debug_info()
        if imgui.begin_popup('op_panel'):
            self.operation_panel()
            imgui.end_popup()
