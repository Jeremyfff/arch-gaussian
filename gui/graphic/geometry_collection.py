from abc import abstractmethod
from typing import Union, Optional

import imgui
import numpy as np

from gui import components as c
from gui.graphic import geometry
from gui.graphic.geometry import BaseGeometry, BaseGeometry3D

SUPPORTED_GEO_TYPES = Union[BaseGeometry, BaseGeometry3D]


class GeometryCollection:

    def __init__(self, camera):
        self.camera = camera
        self.geometries: set[SUPPORTED_GEO_TYPES] = set()

    def add_geometry(self, geo):
        self.geometries.add(geo)
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
    def show_debug_info(self):
        pass


class PointCloudCollection(GeometryCollection):
    def __init__(self, camera, pos_arr=None, color_arr=None):
        super().__init__(camera)

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
        self.point_cloud = self.add_geometry(geometry.PointCloud(pos_arr, color_arr))
        self._debug_num_points = len(pos_arr)

    def show_debug_info(self):
        c.bold_text(f'[{self.__class__.__name__}]')
        imgui.same_line()
        imgui.text(f'num_points: {self._debug_num_points}')
