import datetime
import logging
import queue
from abc import abstractmethod
from typing import Union, Optional

import imgui
import numpy as np
import torch
from pyrr import Vector3

from gui.graphic import geometry
from gui.graphic.geometry import BaseGeometry, BaseGeometry3D
from gui.modules import EventModule
from gui.utils import name_utils, transform_utils

SUPPORTED_GEO_TYPES = Union[BaseGeometry, BaseGeometry3D]

__runtime__ = True
if not __runtime__:
    from src.manager.gaussian_manager import GaussianManager
    from gui.graphic.renderers import IRenderer
    from gui.graphic.geometry import DirectionalLight

class UniqueQueue(queue.Queue):
    def _put(self, item):
        if item not in self.queue:
            queue.Queue._put(self, item)


class IGeometryCollection:

    def __init__(self, name, renderer: "IRenderer"):
        self.name = name
        self.parent_renderer = renderer
        self.camera = renderer.camera
        self.geometries: list[SUPPORTED_GEO_TYPES] = []

        self._geometry_on_enable_queue: UniqueQueue[SUPPORTED_GEO_TYPES] = UniqueQueue()
        self._geometry_on_disable_queue: UniqueQueue[SUPPORTED_GEO_TYPES] = UniqueQueue()

    def add_geometry(self, geo):
        if geo in self.geometries:
            return
        self.geometries.append(geo)
        self._geometry_on_enable_queue.put(geo)
        return geo

    def remove_geometry(self, geo):
        if geo is None:
            return
        if geo not in self.geometries:
            return
        self.geometries.remove(geo)
        self._geometry_on_disable_queue.put(geo)
        return geo

    def clear(self):
        for geo in self.geometries:
            self._geometry_on_disable_queue.put(geo)
        self.geometries.clear()

    def update(self):
        while not self._geometry_on_disable_queue.empty():
            geo = self._geometry_on_disable_queue.get()
            geo.g_on_disable()
        while not self._geometry_on_enable_queue.empty():
            geo = self._geometry_on_enable_queue.get()
            geo.g_on_enable()
        for geo in self.geometries:
            geo.g_update()

    def render(self):
        for geo in self.geometries:
            if geo.active:
                geo.render(self.camera)

    def render_shadowmap(self, dlight: "DirectionalLight"):
        for geo in self.geometries:
            if geo.active:
                geo.render_shadowmap(dlight)

    @abstractmethod
    def operation_panel(self):
        pass

    @abstractmethod
    def show_debug_info(self):
        pass


class SceneBasicCollection(IGeometryCollection):
    """场景的基础信息"""

    def __init__(self, name, renderer: "IRenderer"):
        super().__init__(name, renderer)
        # region geometries
        # opaque
        self.skybox: geometry.SkyBox = self.add_geometry(geometry.SkyBox())
        self.directional_light: geometry.DirectionalLight = self.add_geometry(geometry.DirectionalLight())
        self.axis: geometry.Axis3D = self.add_geometry(geometry.Axis3D())

        # translucent
        self.grid: geometry.Grid3D = self.add_geometry(geometry.Grid3D())

        # endregion

        from gui.user_data import user_data
        self.set_axis_status(user_data.can_show_scene_axis)
        self.set_grid_status(user_data.can_show_scene_grid)
        self.set_skybox_status(user_data.can_show_skybox)

        # region time and shadow
        self.scene_time = SceneTime()
        # endregion

    def operation_panel(self):
        if imgui.tree_node("Scene Time Settings"):
            self.scene_time.operation_panel()
            imgui.tree_pop()
        if imgui.tree_node("Skybox Settings"):
            self.skybox.operation_panel()
            imgui.tree_pop()
        if imgui.tree_node("Directional Light Settings"):
            self.directional_light.operation_panel()
            imgui.tree_pop()

    def show_debug_info(self):
        pass

    def set_axis_status(self, state: bool):
        self.axis.active = state

    def set_grid_status(self, state: bool):
        self.grid.active = state

    def set_skybox_status(self, state: bool):
        self.skybox.active = state


class SceneTime:
    def __init__(self):
        now = datetime.datetime.now()
        self.lat = 33.0
        self.lon = 120.0
        self.year = now.year
        self.month = 1
        self.day = 1
        self.hour = 12
        self.minute = 0
        self.second = 0

        self.light_dir: Vector3 = Vector3((0, 0, 1), dtype="f4")

        self._imgui_year_slider_value = 0.5
        self._imgui_day_slider_value = 0.5
        self.set_time_by_slider()

    def set_time(self, lat, lon, year, month, day, hour, minute, second):
        self.lat = lat
        self.lon = lon
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second

        self._imgui_day_slider_value = (hour * 3600 + minute * 60 + second) / 86399.0
        self._imgui_year_slider_value = (datetime.date(year, month, day) - datetime.date(year, 1, 1)).days / (365.0 if not year % 4 == 0 or (year % 100 == 0 and year % 400 != 0) else 366.0)
        self.light_dir = transform_utils.get_sun_dir(self.lat, self.lon, self.year, self.month, self.day, self.hour, self.minute, self.second)
        EventModule.on_scene_time_change(self)

    def set_time_by_slider(self):
        year = self.year
        day_of_year = int(self._imgui_year_slider_value * (365.0 if not year % 4 == 0 or (year % 100 == 0 and year % 400 != 0) else 366.0))
        start_of_year = datetime.date(year, 1, 1)
        required_date = start_of_year + datetime.timedelta(days=day_of_year - 1)
        self.month = required_date.month
        self.day = required_date.day

        seconds = int(self._imgui_day_slider_value * 86399)
        self.hour = int(seconds // 3600)
        seconds -= self.hour * 3600
        self.minute = int(seconds // 60)
        seconds -= self.minute * 60
        self.second = seconds
        EventModule.on_scene_time_change(self)
        self.light_dir = transform_utils.get_sun_dir(self.lat, self.lon, self.year, self.month, self.day, self.hour, self.minute, self.second)
        EventModule.on_scene_time_change(self)

    def operation_panel(self):
        imgui.text("Set Time: ")

        any_change = False
        changed, lat = imgui.drag_float("lat", self.lat, 0.1, -90, 90)
        any_change |= changed
        changed, lon = imgui.drag_float("lon", self.lon, 0.1, -180, 180)
        any_change |= changed
        changed, year = imgui.drag_int("year", self.year, 1, 0, 5000)
        any_change |= changed
        changed, month = imgui.drag_int("month", self.month, 1, 1, 12)
        any_change |= changed
        changed, day = imgui.drag_int("day", self.day, 1, 1, 31)
        any_change |= changed
        changed, hour = imgui.drag_int("hour", self.hour, 1, 0, 23)
        any_change |= changed
        changed, minute = imgui.drag_int("minute", self.minute, 1, 0, 59)
        any_change |= changed
        changed, second = imgui.drag_int("second", self.second, 1, 0, 59)
        any_change |= changed

        if any_change:
            self.set_time(lat, lon, year, month, day, hour, minute, second)

        changed1, self._imgui_year_slider_value = imgui.slider_float("date slider", self._imgui_year_slider_value, 0.0, 1.0)
        changed2, self._imgui_day_slider_value = imgui.slider_float("time slider", self._imgui_day_slider_value, 0.0, 1.0)
        if changed1 or changed2:
            self.set_time_by_slider()


class PointCloudCollection(IGeometryCollection):
    """一个简单的点云Geometry Collection"""

    def __init__(self, name, renderer: "IRenderer", pos_arr=None, color_arr=None):
        super().__init__(name, renderer)

        if pos_arr is None or color_arr is None:
            num = 100
            pos_arr = np.random.rand(num, 3).astype(np.float32)
            color_arr = np.random.rand(num, 4).astype(np.float32)

        self.num_points = -1

        self.point_cloud: Optional[geometry.PointCloud] = None
        self.set_points_cloud(pos_arr, color_arr)

        # UI
        from gui.graphic.geometry_collection_ui import PointCloudCollectionUI
        self.ui = PointCloudCollectionUI(self)

    def set_points_cloud(self, pos_arr, color_arr):
        pos_arr = pos_arr.astype(np.float32)
        color_arr = color_arr.astype(np.float32)
        self.remove_geometry(self.point_cloud)
        self.point_cloud = self.add_geometry(geometry.PointCloud('point_cloud', pos_arr, color_arr))
        self.num_points = len(pos_arr)

    def delete_self(self):
        self.__init__(self.name, self.camera, None, None)

    def operation_panel(self):
        self.ui.operation_panel()

    def show_debug_info(self):
        self.ui.show_debug_info()


class GaussianCollection(IGeometryCollection):

    def __init__(self, name, renderer: "IRenderer"):

        super().__init__(name, renderer)

        # do not use geometries in GaussianCollection, use self.gaussian_managers instead
        self.gaussian_managers: list["GaussianManager"] = []

        self.final_gm: Optional["GaussianManager"] = None

        # import ui
        from gui.graphic.geometry_collection_ui import GaussianCollectionUI
        self.ui = GaussianCollectionUI(self)

    def set_gaussian_manager(self, gm: "GaussianManager"):
        self.gaussian_managers = []
        if gm is not None:
            self.add_gaussian_manager(gm)
        self.merge_gaussians()

    def add_gaussian_manager(self, gm: "GaussianManager"):
        assert gm is not None
        name = name_utils.ply_path_to_model_name(gm.source_ply_path)
        self.gaussian_managers.append(gm)

    def remove_gaussian_manager(self, gm: "GaussianManager"):
        assert gm is not None
        if gm in self.gaussian_managers:
            self.gaussian_managers.remove(gm)

    def merge_gaussians(self):
        from src.manager.gaussian_manager import GaussianManager
        self.final_gm = GaussianManager.merge_gaussian_managers(self.gaussian_managers)

    def render_gaussian(self, opaque_depth: torch.Tensor) -> Optional[torch.Tensor]:
        if self.final_gm is None:
            return None
        return self.final_gm.render_fork(camera=self.camera, opaque_depth=opaque_depth)

    def render(self):
        super().render()
        logging.error("you are rendering gaussian point clouds, to rasterize gaussians, use ~.render_gaussian method")

    def operation_panel(self):
        self.ui.operation_panel()

    def show_debug_info(self):
        self.ui.show_debug_info()


class DebugCollection(IGeometryCollection):
    """用于显示各种debug物体, 这是一种特殊的collection， 其物体每帧刷新"""

    def __init__(self, name, renderer: "IRenderer"):
        super().__init__(name, renderer)

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


class EditableGeometryCollection(IGeometryCollection):
    """
    可编辑的Geometry Collection， 提供编辑方法
    """

    def __init__(self, name, renderer: "IRenderer"):
        super().__init__(name, renderer)

        # UI
        from gui.graphic.geometry_collection_ui import EditableGeometryCollectionUI
        self.ui = EditableGeometryCollectionUI(self)

    def operation_panel(self):
        self.ui.operation_panel()

    def show_debug_info(self):
        self.ui.show_debug_info()
