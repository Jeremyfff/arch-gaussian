import logging
import os
import uuid
from abc import abstractmethod
from functools import cached_property
from typing import Optional, Union, Type

import imgui
import moderngl
import numpy as np
from moderngl_window import geometry
from moderngl_window.geometry.attributes import AttributeNames
from moderngl_window.opengl.vao import VAO
from moderngl_window.scene.camera import Camera
from objloader import Obj
from pyrr import Vector3, Vector4, Matrix44

from gui.global_app_state import g
from gui.global_info import RESOURCES_DIR
from gui.graphic import geometry_component
from gui.graphic import geometry_ui
from gui.graphic.material import MaterialInstance, Material, IMaterial
from gui.graphic.material_lib import MaterialLib
from gui.modules import EventModule
from gui.user_data import user_settings

__runtime__ = True
if not __runtime__:
    from gui.graphic.geometry_collection import SceneTime


def generate_x_lines(size, gap=0.5, z_pos=.0):
    # 生成 x 方向上每条线的起点和终点坐标

    x_start = np.arange(-size, size + gap * 0.5, gap)  # x 起点坐标
    num = len(x_start)
    y_start = np.zeros(num) - size  # y 起点坐标
    z_start = np.zeros(num) + z_pos  # z 起点坐标

    x_end = x_start  # x 终点坐标与起点相同
    y_end = y_start + size * 2  # y 终点坐标偏移 4
    z_end = z_start + z_pos  # z 终点坐标与起点相同

    # 组合起点和终点坐标
    start_points = np.column_stack((x_start, y_start, z_start))
    end_points = np.column_stack((x_end, y_end, z_end))

    # 将起点-终点坐标按照起点-终点-起点-终点...的顺序排列
    points = np.array([[start, end] for start, end in zip(start_points, end_points)]).reshape(-1, 2, 3)

    return points


def generate_y_lines(size, gap=0.5, z_pos=.0):
    # 生成 y 方向上每条线的起点和终点坐标

    y_start = np.arange(-size, size + gap * 0.5, gap)  # y 起点坐标
    num = len(y_start)
    x_start = np.zeros(num) - size  # x 起点坐标
    z_start = np.zeros(num) + z_pos  # z 起点坐标

    y_end = y_start  # y 终点坐标与起点相同
    x_end = x_start + size * 2  # x 终点坐标偏移 4
    z_end = z_start + z_pos  # z 终点坐标与起点相同

    # 组合起点和终点坐标
    start_points = np.column_stack((x_start, y_start, z_start))
    end_points = np.column_stack((x_end, y_end, z_end))

    # 将起点-终点坐标按照起点-终点-起点-终点...的顺序排列
    points = np.array([[start, end] for start, end in zip(start_points, end_points)]).reshape(-1, 2, 3)

    return points


class BaseGeometry:
    def __init__(self, name):
        self.uid = str(uuid.uuid4())
        self.ctx = g.mWindowEvent.ctx
        self._name = name
        self._active = True
        self._components: list[geometry_component.IComponent] = []
        self._material: Optional[IMaterial] = None

    # region Events
    def g_update(self):
        for component in self._components:
            component.update()

    def g_on_enable(self):
        for component in self._components:
            component.on_enable()

    def g_on_disable(self):
        for component in self._components:
            component.on_disable()

    # endregion

    # region Rendering
    def render_shadowmap(self, dlight: "DirectionalLight"):
        pass

    @abstractmethod
    def render(self, camera: Camera):
        raise NotImplementedError("This method (render) should be overwritten by child Classes")

    # endregion

    # region properties
    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, active):
        if active != self._active:
            self._active = active
            self._on_active_changed()

    def _on_active_changed(self):
        logging.info(f"[{self.name}] active state changed to {self._active}")
        if self._active:
            self.g_on_enable()
        else:
            self.g_on_disable()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name != self._name:
            self._name = name
            self._on_name_changed()

    def _on_name_changed(self):
        logging.info(f"[{self.name}] name changed to {self._name}")

    # endregion

    # region Components
    @property
    def components(self):
        return self._components

    def add_component(self, component: geometry_component.IComponent):
        if component in self._components:
            return
        self._components.append(component)
        component.on_enable()

    def remove_component(self, component: geometry_component.IComponent):
        if component not in self._components:
            return
        self._components.remove(component)
        component.on_disable()

    def get_component(self, cls: Type[geometry_component.IComponent]):
        for component in self._components:
            if isinstance(component, cls):
                return component
        return None

    # endregion

    # region Material
    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, mat: IMaterial):
        self._material = mat

    # endregion

    # region Misc
    def is_points_inside(self, points):
        raise NotImplementedError("This method (is_points_inside) should be overwritten by child Classes")

    # endregion

    # region UI
    @abstractmethod
    def operation_panel(self):
        raise NotImplementedError

    # endregion


class BaseGeometry3D(BaseGeometry):
    """
    继承自BaseGeometry， 提供渲染三维空间中物体的能力
    默认需要提供shader代码，VAO对象（可选）， 渲染模式

    提供了默认的渲染方法

    操作面板提供了平移旋转缩放对象的功能

    """

    def __init__(self, name, material: Optional[IMaterial] = None, vao: Optional[VAO] = None, mode=moderngl.TRIANGLES):
        super().__init__(name)
        self._vao: VAO = vao if vao is not None else VAO(name, mode=mode)
        if material is None:
            material = MaterialLib.GetDefaultMat_Lit().copy(f"_Mat_{name}")
        self.material = material

        # init components
        self._transform = geometry_component.TransformComponent(self)
        self._components.append(self._transform)

        # 提前确定render function， 减少分支预测
        if self.material.support_mvp:
            self._render_function = self._render_function_1
        elif self.material.support_m:
            self._render_function = self._render_function_2
        else:
            raise Exception
        self._render_target_material = self.material

        self._ui = geometry_ui.GeometryUITemplate(self)

    @property
    def transform(self):
        return self._transform

    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, value: IMaterial):
        assert value.support_m
        self._material = value

    def render_shadowmap(self, dlight: "DirectionalLight"):
        if not self.material.cast_shadows:
            return
        self._render_function(self.material.shadowmap_mat, dlight.m_camera, dlight.m_projection)

    def render(self, camera: Camera):
        self.before_render(camera)
        self._render_function(self.material, camera.matrix, camera.projection.matrix)
        self.after_render(camera)

    def _render_function_1(self, material: Material, m_camera, m_proj):
        material.write_mvp(self.transform.model_view_with_no_world_matrix, m_camera, m_proj)
        material.use()
        self._vao.render(material.prog)

    def _render_function_2(self, material, m_camera, m_proj):
        material.write_m(self.transform.model_view_with_no_world_matrix)
        material.use()
        self._vao.render(material.prog)

    def before_render(self, camera: Camera):
        pass

    def after_render(self, camera: Camera):
        pass

    def operation_panel(self):
        return self._ui.operation_panel()


class PointCloud(BaseGeometry3D):
    def __init__(self, name, pos_arr: np.ndarray, color_arr: np.ndarray, material: Union[IMaterial, Material, MaterialInstance, None] = None):
        """color_arr should be in range(0, 1)"""
        _rgba = False
        if material is None:
            if color_arr.shape[1] == 4:
                _rgba = True
                material = MaterialLib.GetDefaultMat_PtCloudRGBA()
            elif color_arr.shape[1] == 3:
                _rgba = False
                material = MaterialLib.GetDefaultMat_PtCloudRGB()

        super().__init__(name, material, mode=moderngl.POINTS)
        self._vao.buffer(pos_arr, '3f', ['in_position'])
        self._vao.buffer(color_arr, '4f' if _rgba else '3f', ['in_color'])

        self.bbox = np.vstack((np.min(pos_arr, axis=0), np.max(pos_arr, axis=0)))

    @abstractmethod
    def operation_panel(self):
        return super().operation_panel()


class Line3D(BaseGeometry3D):
    def __init__(self, name: Optional[str] = None, points: Union[tuple, np.ndarray] = None, material: Optional[IMaterial] = None, mode=moderngl.LINES):
        if name is None:
            name = str(uuid.uuid4())
        if points is None:
            points = ((0, 0, 0),)
        if not isinstance(points, np.ndarray):
            points = np.array(points, dtype=np.float32)
        elif points.dtype != np.float32:
            points = points.astype(np.float32)
        if material is None:
            material = MaterialLib.GetDefaultMat_LineRGBA()
        super().__init__(name=name, material=material, vao=None, mode=mode)
        self.points = points
        self.points_buffer = self._vao.buffer(self.points, '3f', [AttributeNames.POSITION])

    def set_points(self, points: Union[tuple, np.ndarray]):
        if not isinstance(points, np.ndarray):
            points = np.array(points, dtype=np.float32)
        elif points.dtype != np.float32:
            points = points.astype(np.float32)
        assert len(points) == len(self.points)
        self.points = points
        # self.points_buffer = self.vao.buffer(points, '3f', [AttributeNames.POSITION])
        self.points_buffer.write(self.points.tobytes())


class WiredBoundingBox(Line3D):

    def __init__(self, name, bound_min, bound_max, material=None):
        edges = self._generate_edges(bound_min, bound_max)

        super().__init__(name, points=edges, material=material, mode=moderngl.LINES)
        self.bound_min = bound_min
        self.bound_max = bound_max

    def _generate_edges(self, bound_min, bound_max):
        _ = self
        minx = bound_min[0]
        miny = bound_min[1]
        minz = bound_min[2]
        maxx = bound_max[0]
        maxy = bound_max[1]
        maxz = bound_max[2]
        edges = np.array((
            (minx, miny, minz), (minx, miny, maxz),
            (minx, miny, minz), (minx, maxy, minz),
            (minx, miny, minz), (maxx, miny, minz),
            (maxx, maxy, maxz), (maxx, miny, maxz),
            (maxx, maxy, maxz), (minx, maxy, maxz),
            (maxx, maxy, maxz), (maxx, maxy, minz),
            (minx, miny, maxz), (maxx, miny, maxz),
            (minx, miny, maxz), (minx, maxy, maxz),
            (maxx, maxy, minz), (minx, maxy, minz),
            (maxx, maxy, minz), (maxx, miny, minz),
            (maxx, miny, maxz), (maxx, miny, minz),
            (minx, maxy, maxz), (minx, maxy, minz)
        ), dtype=np.float32)
        return edges

    def set_bound_min(self, bound_min):
        self.__init__(self.name, bound_min, self.bound_max, self._material)

    def set_bound_max(self, bound_max):
        self.__init__(self.name, self.bound_min, bound_max, self._material)

    def operation_panel(self):
        changed, delete_self = super().operation_panel()
        return changed, delete_self

    def is_points_inside(self, points):
        import torch
        if not isinstance(points, torch.Tensor):
            points = torch.tensor(points)
        if not points.is_cuda:
            points = points.cuda()
        if len(points.shape) == 1:
            points = points.reshape(1, -1)
        assert len(points.shape) == 2
        model_view = torch.tensor(self.transform.model_view_with_no_world_matrix).cuda()
        with torch.no_grad():
            inverse_model_view = torch.inverse(model_view)

            # 将点云坐标扩展到齐次坐标系
            homogeneous_points = torch.cat((points, torch.ones((points.shape[0], 1), dtype=torch.float, device="cuda")),
                                           dim=1)

            # 使用逆矩阵 inverse_model_view 进行逆变换
            transformed_points = torch.matmul(homogeneous_points, inverse_model_view)

            # 将变换后的点坐标恢复至三维坐标
            restored_points = transformed_points[:, :3] / transformed_points[:, 3].reshape(-1, 1)

            # 判断 x、y、z 是否都分别小于指定的阈值
            condition_x1 = self.bound_min[0] < restored_points[:, 0]
            condition_x2 = restored_points[:, 0] < self.bound_max[0]
            condition_y1 = self.bound_min[1] < restored_points[:, 1]
            condition_y2 = restored_points[:, 1] < self.bound_max[1]
            condition_z1 = self.bound_min[2] < restored_points[:, 2]
            condition_z2 = restored_points[:, 2] < self.bound_max[2]

            # 使用逻辑与运算符 & 将所有条件合并
            combined_condition = condition_x1 & condition_x2 & condition_y1 & condition_y2 & condition_z1 & condition_z2

        return combined_condition

    def before_render(self, camera: Camera):
        pass

    def after_render(self, camera: Camera):
        pass


class Polygon(Line3D):

    def __init__(self, name, points: np.ndarray, material=None, closed=True):
        # points = (n, 3)
        assert len(points.shape) == 2
        assert points.shape[1] == 3  # 三维点
        if closed:
            points = np.vstack((points, points[0]))
        super().__init__(name=name, points=points, material=material, mode=moderngl.LINE_STRIP)
        self.points = points

    def is_points_inside(self, points):
        import torch
        if not isinstance(points, torch.Tensor):
            points = torch.tensor(points)
        if not points.is_cuda:
            points = points.cuda()
        if len(points.shape) == 1:
            points = points.reshape(1, -1)
        assert len(points.shape) == 2
        model_view = torch.tensor(self.transform.model_view_with_no_world_matrix).cuda()
        with torch.no_grad():
            inverse_model_view = torch.inverse(model_view)

            # 将点云坐标扩展到齐次坐标系
            homogeneous_points = torch.cat((points, torch.ones((points.shape[0], 1), dtype=torch.float, device="cuda")),
                                           dim=1)

            # 使用逆矩阵 inverse_model_view 进行逆变换
            transformed_points = torch.matmul(homogeneous_points, inverse_model_view)

            # 将变换后的点坐标恢复至三维坐标
            restored_points = transformed_points[:, :3] / transformed_points[:, 3].reshape(-1, 1)
            restored_points_2d = restored_points[:, :2]  # (n, 2)

            polyline_points_2d = torch.tensor(self.points[:, :2]).cuda()  # (num_polygon_points, 2)
            conditions = []  # (num_polygon_points, num_points)
            for i in range(len(self.points) - 1):
                line_vector = polyline_points_2d[i + 1] - polyline_points_2d[i]  # (2, )
                line_to_vector = restored_points_2d - polyline_points_2d[i]  # (num_points, 2)
                cross_value = line_vector[0] * line_to_vector[:, 1] - line_vector[1] * line_to_vector[:, 0]
                # print(cross_value.shape)  # (num_points, )
                condition = cross_value > 0
                conditions.append(condition)
            conditions = torch.stack(conditions, dim=1)
            combined_condition1 = conditions.all(dim=1)
            combined_condition2 = ~conditions.any(dim=1)
            combined_condition = combined_condition1 | combined_condition2
        return combined_condition

    def operation_panel(self):
        pass

    def before_render(self, camera: Camera):
        pass

    def after_render(self, camera: Camera):
        pass


class Axis3D(BaseGeometry):
    """时多个BaseGeometry3D的集合，因此继承BaseGeometry"""

    def __init__(self, name='axis3d'):
        super().__init__(name)
        mat = MaterialLib.GetDefaultMat_LineRGBA()
        mat_r = mat.copy("_DefaultMat_AxisX")
        mat_g = mat.copy("_DefaultMat_AxisY")
        mat_b = mat.copy("_DefaultMat_AxisZ")

        self.axis_x = Line3D(points=((0, 0, 0), (100, 0, 0)), material=mat_r)
        self.axis_x.material['color'] = (1, 0, 0, 1)

        self.axis_y = Line3D(points=((0, 0, 0), (0, 100, 0)), material=mat_g)
        self.axis_y.material['color'] = (0, 1, 0, 1)

        self.axis_z = Line3D(points=((0, 0, 0), (0, 0, 100)), material=mat_b)
        self.axis_z.material['color'] = (0, 0, 1, 1)

    def render_shadowmap(self, dlight: "DirectionalLight"):
        pass

    def render(self, camera: Camera):
        self.axis_x.render(camera)
        self.axis_y.render(camera)
        self.axis_z.render(camera)

    @abstractmethod
    def operation_panel(self):
        imgui.text("nothing to show")
        return False, False


class Grid3D(BaseGeometry):

    def __init__(self, name='grid3d'):
        super().__init__(name)

        x_lines = generate_x_lines(10, 1)
        y_lines = generate_y_lines(10, 1)
        grid_pts_level0 = np.vstack((x_lines, y_lines))

        x_lines = generate_x_lines(10, 0.1)
        y_lines = generate_y_lines(10, 0.1)
        grid_pts_level1 = np.vstack((x_lines, y_lines))

        mat_level0 = MaterialLib.GetDefaultMat_GridLine().copy("_DefaultMat_GridLine_Level0")
        mat_level1 = MaterialLib.GetDefaultMat_GridLine().copy("_DefaultMat_GridLine_Level1")
        self.grid_level0 = Line3D(points=grid_pts_level0,
                                  name="grid_level_0",
                                  mode=moderngl.LINES,
                                  material=mat_level0)
        self.grid_level0.material['color'] = (0.5, 0.5, 0.5, 0.8)

        self.grid_level1 = Line3D(points=grid_pts_level1,
                                  name="grid_level_1",
                                  mode=moderngl.LINES,
                                  material=mat_level1)
        self.grid_level1.material['color'] = (0.5, 0.5, 0.5, 0.4)
        self._set_prog()

    def render_shadowmap(self, dlight: "DirectionalLight"):
        pass

    def render(self, camera: Camera):
        if g.mIsUserSettingsContentOpen:
            # 如果设置面板打开，则更新参数
            self._set_prog()

        camPosWS = tuple(camera.position.tolist())
        self.grid_level0.material['camPosWS'] = camPosWS
        self.grid_level1.material['camPosWS'] = camPosWS
        self.grid_level0.render(camera)
        self.grid_level1.render(camera)

    def _set_prog(self):
        self.grid_level0.material['maxDist'] = user_settings.grid_fading_distance
        self.grid_level1.material['maxDist'] = user_settings.grid_fading_distance
        self.grid_level0.translation = (0.0, 0.0, -user_settings.grid_z_offset)
        self.grid_level1.translation = (0.0, 0.0, -user_settings.grid_z_offset * 2)

    def operation_panel(self):
        raise NotImplementedError


class Mesh3D(BaseGeometry3D):
    def __init__(self,
                 name,
                 file_path: str,
                 material: Optional[IMaterial] = None,
                 normal=True,
                 uv=True):
        if not file_path.endswith(".obj"):
            raise Exception("file must be .obj")
        super().__init__(name, material=material, vao=None, mode=moderngl.TRIANGLES)

        obj = Obj.open(file_path)
        in_position_buffer = self.ctx.buffer(obj.pack('vx vy vz'))
        self._vao.buffer(in_position_buffer, "3f", [AttributeNames.POSITION])
        if normal:
            in_normal_buffer = self.ctx.buffer(obj.pack('nx ny nz'))
            self._vao.buffer(in_normal_buffer, "3f", [AttributeNames.NORMAL])
        if uv:
            in_texcoord_0_buffer = self.ctx.buffer(obj.pack('tx ty'))
            self._vao.buffer(in_texcoord_0_buffer, "2f", [AttributeNames.TEXCOORD_0])
        # self.parent_rotation = (-math.pi / 2, 0, 0)


class SimpleCube(BaseGeometry3D):
    def __init__(self, name, material=None, size=(1, 1, 1)):
        if material is None:
            material = MaterialLib.GetDefaultMat_Lit().copy(f"_Mat_{name}")
        super().__init__(name, material=material, vao=geometry.cube(size))
        self.size = size

    @abstractmethod
    def operation_panel(self):
        return super().operation_panel()

    def is_points_inside(self, points):
        import torch
        if not isinstance(points, torch.Tensor):
            points = torch.tensor(points)
        if not points.is_cuda:
            points = points.cuda()
        if len(points.shape) == 1:
            points = points.reshape(1, -1)
        assert len(points.shape) == 2
        model_view = torch.tensor(self.transform.model_view_with_no_world_matrix).cuda()
        with torch.no_grad():
            inverse_model_view = torch.inverse(model_view)

            # 将点云坐标扩展到齐次坐标系
            homogeneous_points = torch.cat((points, torch.ones((points.shape[0], 1), dtype=torch.float, device="cuda")),
                                           dim=1)

            # 使用逆矩阵 inverse_model_view 进行逆变换
            transformed_points = torch.matmul(homogeneous_points, inverse_model_view)

            # 将变换后的点坐标恢复至三维坐标
            restored_points = transformed_points[:, :3] / transformed_points[:, 3].reshape(-1, 1)

            # 对坐标进行绝对值操作
            absolute_points = torch.abs(restored_points)

            # 判断 x、y、z 是否都分别小于指定的阈值
            condition_x = absolute_points[:, 0] < self.size[0] / 2
            condition_y = absolute_points[:, 1] < self.size[1] / 2
            condition_z = absolute_points[:, 2] < self.size[2] / 2

            # 使用逻辑与运算符 & 将所有条件合并
            combined_condition = condition_x & condition_y & condition_z

        return combined_condition


class Polygon3D(BaseGeometry3D):
    def __init__(self, name, points: np.ndarray, z_min, z_max, material=None, closed=True):
        assert len(points.shape) == 2
        assert points.shape[1] == 3  # 三维点
        assert z_max > z_min
        if material is None:
            material = MaterialLib.GetDefaultMat_Unlit()
        super().__init__(name, material=material, vao=None, mode=moderngl.TRIANGLES)
        self.z_min = z_min
        self.z_max = z_max

        if closed:
            points = np.vstack((points, points[0]))
        self.points = points  # 始终为首尾相连的
        min_points = np.array(points)
        min_points[:, 2] = z_min
        max_points = np.array(points)
        max_points[:, 2] = z_max
        min_points = min_points.astype(np.float32)
        max_points = max_points.astype(np.float32)
        num_faces = len(points) - 1
        vertices = np.empty(shape=(6 * num_faces, 3), dtype=np.float32)
        for i in range(num_faces):
            vertices[6 * i + 0] = min_points[i + 1]
            vertices[6 * i + 1] = max_points[i]
            vertices[6 * i + 2] = min_points[i]
            vertices[6 * i + 3] = max_points[i + 1]
            vertices[6 * i + 4] = max_points[i]
            vertices[6 * i + 5] = min_points[i + 1]
        self._vao.buffer(vertices, '3f', [AttributeNames.POSITION])

    def operation_panel(self):
        return super().operation_panel()

    def is_points_inside(self, points):
        import torch
        if not isinstance(points, torch.Tensor):
            points = torch.tensor(points)
        if not points.is_cuda:
            points = points.cuda()
        if len(points.shape) == 1:
            points = points.reshape(1, -1)
        assert len(points.shape) == 2
        model_view = torch.tensor(self.transform.model_view_with_no_world_matrix).cuda()
        with torch.no_grad():
            inverse_model_view = torch.inverse(model_view)

            # 将点云坐标扩展到齐次坐标系
            homogeneous_points = torch.cat((points, torch.ones((points.shape[0], 1), dtype=torch.float, device="cuda")),
                                           dim=1)

            # 使用逆矩阵 inverse_model_view 进行逆变换
            transformed_points = torch.matmul(homogeneous_points, inverse_model_view)

            # 将变换后的点坐标恢复至三维坐标
            restored_points = transformed_points[:, :3] / transformed_points[:, 3].reshape(-1, 1)
            restored_points_2d = restored_points[:, :2]  # (n, 2)

            polyline_points_2d = torch.tensor(self.points[:, :2]).cuda()  # (num_polygon_points, 2)
            conditions = []  # (num_polygon_points, num_points)
            for i in range(len(self.points) - 1):
                line_vector = polyline_points_2d[i + 1] - polyline_points_2d[i]  # (2, )
                line_to_vector = restored_points_2d - polyline_points_2d[i]  # (num_points, 2)
                cross_value = line_vector[0] * line_to_vector[:, 1] - line_vector[1] * line_to_vector[:, 0]
                # print(cross_value.shape)  # (num_points, )
                condition = cross_value > 0
                conditions.append(condition)
            conditions = torch.stack(conditions, dim=1)
            combined_condition1 = conditions.all(dim=1)
            combined_condition2 = ~conditions.any(dim=1)
            combined_condition = combined_condition1 | combined_condition2
            z_condition1 = self.z_min < restored_points[2]
            z_condition2 = self.z_max > restored_points[2]
            final_condition = combined_condition & z_condition1 & z_condition2
        return final_condition


class QuadFullScreen(BaseGeometry):
    def __init__(self, name, material=None):
        super().__init__(name)
        self.ctx = g.mWindowEvent.ctx
        self.vao: VAO = geometry.quad_fs()
        if material is None:
            material = MaterialLib.GetDefaultMat_Unlit()
        self.material = material

    @property
    def prog(self):
        return self.material.prog

    def render(self, camera: None = None):
        _ = camera
        self.material.use()
        self.vao.render(self.material.prog)

    @abstractmethod
    def operation_panel(self):
        return super().operation_panel()


# class GaussianPointCloud(BaseGeometry):
#     """包裹了一个gaussian manager 和 PointCloud的geometry"""
#
#     def __init__(self, name, gaussian_manager=None, debug_collection=None):
#         super().__init__(name)
#         # 维护的对象
#         # 1. gaussian manager
#         from src.manager.gaussian_manager import GaussianManager
#         self.gm: Optional[GaussianManager] = gaussian_manager
#         from gui.contents import ViewerContent
#         self.ViewerContentClass = ViewerContent
#         # # 2. gaussian point cloud
#         # self.gaussian_point_cloud: Optional[PointCloud] = None
#
#         # debug collection
#         from gui.graphic.geometry_collection import DebugCollection
#         self.debug_collection: Optional[DebugCollection] = debug_collection  # 用于显示各种debug信息
#         # 3. debug bbox
#         self.debug_bbox: Optional[WiredBoundingBox] = None
#
#         # 几何变换等信息
#         self.transition = np.zeros((3,), dtype=np.float32)
#         self.rotation = np.zeros((3,), dtype=np.float32)
#         # 其他信息
#         self._imgui_transition = (0, 0, 0)
#         self._imgui_rotation = (0, 0, 0)  # degree
#         self._imgui_show_debug_bbox = True  # 显示bbox
#
#         # 缓存信息
#         pass
#
#     def update_debug_geometries_matrix_model(self):
#         """当self的位置和旋转改变时， 更新对应的debug geometries的位置和旋转"""
#         self.debug_bbox.parent_translation = self.transition
#         self.debug_bbox.parent_rotation = self.rotation
#
#     # def update_gaussian_points_matrix_model(self):
#     #     """当自身的位置和旋转改变时， 更新对应的point cloud的位置和旋转"""
#     #     self.gaussian_point_cloud.translation = self.transition
#     #     self.gaussian_point_cloud.rotation = self.rotation
#
#     # def generate_gaussian_points(self):
#     #     """根据gm中的gaussians的点云数据更新自身的PointCloud"""
#     #     if self.gm is None:
#     #         logging.warning('no gaussian manger')
#     #         return
#     #     # 重置变换信息
#     #     self.transition = np.zeros((3,), dtype=np.float32)
#     #     self.rotation = np.zeros((3,), dtype=np.float32)  # rad
#     #     self._imgui_transition = (0, 0, 0)
#     #     self._imgui_rotation = (0, 0, 0)  # degree
#     #
#     #     # 根据现在gaussian manager中的点重新创建point cloud
#     #     logging.info(f'updating gaussian points')
#     #     pos_arr = self.gm.gaussians.get_xyz.detach().cpu().numpy()  # (n, 3)
#     #     rgb_arr = self.gm.gaussians.get_features_dc.detach().cpu().numpy().squeeze(axis=1)  # (n, 3)
#     #     alpha_arr = self.gm.gaussians.get_alpha.detach().cpu().numpy().squeeze(axis=1)
#     #     rgba = np.hstack((rgb_arr, alpha_arr.reshape(-1, 1)))
#     #     SH_C0 = 0.28209479177387814
#     #     rgba[:, 0:3] = (0.5 + SH_C0 * rgba[:, 0:3])
#     #     rgba[:, 3] = (1 / (1 + np.exp(-rgba[:, 3])))
#     #     rgba = np.clip(rgba, 0.0, 1.0)
#     #     self.gaussian_point_cloud = PointCloud(f'{self.name}_point_cloud', pos_arr, rgba)
#     #     # 更新其他debug geometries
#     #     # bbox被重新生成
#     #     bbox = self.gaussian_point_cloud.bbox
#     #     self.debug_bbox = WiredBoundingBox(f'{self.name}_bbox', bbox[0], bbox[1])
#
#     def show_debug_info(self):
#         c.bold_text(f'[{self.__class__.__name__}(class)]')
#
#     def operation_panel(self, is_the_only_geo=False) -> tuple:
#
#         """
#         高斯几何体的操作面板
#         return (changed, delete_self)
#         """
#         # region outputs
#         delete_self = False  # to tell the parent collection to delete self
#         changed = False
#         # endregion
#
#         imgui.push_id(self.uid)
#         # region 标题栏、删除按钮
#         self.imgui_title_bar_template()
#         if c.icon_text_button('delete-bin-fill', 'Delete Gaussian', uid=f"delete gaussian button {self.uid}"):
#             delete_self = True
#             changed |= True
#         # endregion
#         # region 更新GAUSSIAN POINTS
#         # if imgui.button('Update Gaussian Points'):
#         #     self.generate_gaussian_points()
#         #     changed |= True
#         # c.easy_tooltip('Manually update gaussian points base on GaussianManager.gaussians')
#         # endregion
#         imgui.separator()
#         # region GAUSSIAN MANAGER STUFF, TRANSITION, ROTATION AND OTHERS
#         if imgui.button("cache"):
#             self.gm.cache()
#
#         if self.gm.gaussians_backup is not None:
#             imgui.same_line()
#             if imgui.button("restore"):
#                 self.gm.restore()
#             imgui.same_line()
#             if imgui.button("apply"):
#                 self.gm.apply()
#         else:
#             StyleModule.push_disabled_button_color()
#             imgui.same_line()
#             imgui.button("restore")
#             imgui.same_line()
#             imgui.button("apply")
#             StyleModule.pop_button_color()
#
#         transition_changed, self._imgui_transition = imgui.drag_float3(
#             'transition', *self._imgui_transition, user_settings.move_scroll_speed)
#         if imgui.is_item_deactivated_after_edit() or (is_the_only_geo and transition_changed):
#             offset = np.array(self._imgui_transition, dtype=np.float32) - self.transition
#             self.gm.move(offset)
#             self.transition = np.array(self._imgui_transition, dtype=np.float32)
#             changed |= True
#
#         rotation_changed, self._imgui_rotation = imgui.drag_float3('rotation', *self._imgui_rotation, 1.0)
#         if imgui.is_item_deactivated_after_edit() or (is_the_only_geo and rotation_changed):
#             org_rotation_matrix = Matrix44.from_eulers(self.rotation)
#             new_rotation_matrix = Matrix44.from_eulers(np.array(self._imgui_rotation) * math.pi / 180)
#             rotation_matrix = new_rotation_matrix @ org_rotation_matrix.inverse
#             self.gm.rotate(rotation_matrix)
#             self.rotation = np.array(self._imgui_rotation, dtype=np.float32) / 180.0 * math.pi  # convert to rad
#             changed |= True
#         if changed:
#             # self.update_gaussian_points_matrix_model()
#             self.update_debug_geometries_matrix_model()
#         # endregion
#
#         imgui.pop_id()
#
#         # debug collection
#         if self.debug_collection is not None:
#             if self._imgui_show_debug_bbox:
#                 self.debug_collection.draw_bbox(self.debug_bbox, skip_examine=True)
#
#         return changed, delete_self
#
#     def render(self, camera: Camera):
#         # self.gaussian_point_cloud.render(camera)
#         raise Exception


class SkyBox(Mesh3D):

    def __init__(self):
        super().__init__("SkyBox",
                         os.path.join(RESOURCES_DIR, "models/unit_sphere_inv.obj"),
                         MaterialLib.GetDefaultMat_SkyBox(),
                         normal=True,
                         uv=True)
        EventModule.register_scene_time_change_callback(self._on_scene_time_changed)

    def __del__(self):
        EventModule.unregister_scene_time_change_callback(self._on_scene_time_changed)

    def before_render(self, camera: Camera):
        far = camera.projection.far * 0.8
        self.transform.scale = (far, far, far)
        self.transform.translation = self.transform.from_gl_space(camera.position)

    def after_render(self, camera: Camera):
        pass

    def is_points_inside(self, points):
        raise NotImplementedError

    def _on_scene_time_changed(self, scene_time: "SceneTime"):
        self._material["_LightDir"] = scene_time.light_dir.astype("f4")


class DirectionalLight(Line3D):

    def __init__(self):
        super().__init__("DirectionalLight", ((0, 0, 0), (0, 0, 1)))
        self.direction: Vector3 = Vector3((0, 0, 1), dtype="f4")

        self._color: Vector3 = Vector3((1, 1, 1), dtype="f4")
        self._range: float = 5.0

        # region components
        self.directional_light_component = geometry_component.DirectionalLightComponent(self)
        self._components.append(self.directional_light_component)
        # endregion

        # region ui configuration
        self._ui.show_material = False
        self._ui.show_components = True
        self._ui.show_delete_self_button = False
        self._ui.editable_name = False
        # endregion

        # region Events
        EventModule.register_scene_time_change_callback(self._on_scene_time_change)

    def __del__(self):
        EventModule.unregister_scene_time_change_callback(self._on_scene_time_change)

    def _on_scene_time_change(self, scene_time: "SceneTime"):
        self.direction = scene_time.light_dir.astype("f4")
        self.set_points(([0, 0, 0], self.direction * 10))
        self._clear_m_camera_cache()

    def _clear_m_projection_cache(self):
        if "m_projection" in self.__dict__:
            self.__dict__.pop("m_projection")
        if "m_depth" in self.__dict__:
            self.__dict__.pop("m_depth")

    def _clear_m_camera_cache(self):
        if "m_camera" in self.__dict__:
            self.__dict__.pop("m_camera")
        if "m_depth" in self.__dict__:
            self.__dict__.pop("m_depth")

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value: Vector4):
        self._color = value

    @property
    def range(self) -> float:
        return self._range

    @range.setter
    def range(self, value):
        self._range = value
        self._clear_m_projection_cache()

    @cached_property
    def m_projection(self) -> Matrix44:
        depth_projection = Matrix44.orthogonal_projection(-self.range, self.range, -self.range, self.range, -self.range * 2, self.range * 2, "f4")
        # depth_projection = glm.ortho(-self.range, self.range, -self.range, self.range, -self.range * 2, self.range * 2)
        return depth_projection

    @cached_property
    def m_camera(self) -> Matrix44:
        gl_cam_pos = self.transform.to_gl_space(self.transform.world_translation)
        gl_target_pos = self.transform.to_gl_space(self.transform.world_translation + self.direction)
        return Matrix44.look_at(gl_cam_pos, gl_target_pos, self.transform.gl_up, "f4")

    @cached_property
    def bias_matrix(self) -> Matrix44:
        return Matrix44((
            (0.5, 0.0, 0.0, 0.0),
            (0.0, 0.5, 0.0, 0.0),
            (0.0, 0.0, 0.5, 0.0),
            (0.5, 0.5, 0.5, 1.0),
        ), dtype="f4")

    @cached_property
    def m_depth(self) -> Matrix44:
        _m_depth = self.bias_matrix * self.m_projection * self.m_camera * self.transform.world_matrix
        return _m_depth

    def render(self, camera: Camera):
        if self.directional_light_component.show_indicator:
            super().render(camera)
