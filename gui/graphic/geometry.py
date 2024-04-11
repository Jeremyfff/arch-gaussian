import logging
import math
import uuid
from abc import abstractmethod
from typing import Optional

import imgui
import moderngl
import numpy as np
from moderngl_window import geometry
from moderngl_window.opengl.vao import VAO
from moderngl_window.scene.camera import Camera
from pyrr import Matrix44

from gui import components as c
from gui import global_userinfo
from gui import global_var as g
from gui.modules import StyleModule


class BaseGeometry:
    @abstractmethod
    def __init__(self, name):
        self.uid = str(uuid.uuid4())
        self.name = name
        self.active = True

        # imgui变量

        self._imgui_name_variable = self.name
        self._imgui_editing_name = False

    @abstractmethod
    def render(self, camera: Camera):
        pass

    @abstractmethod
    def operation_panel(self):
        """提供了一个基础样板, 可以直接继承，也可以自定义-
        return (changed, delete_self)
        """

        delete_self = False  # to tell the parent collection to delete self
        changed = False
        imgui.push_id(self.uid)
        self.imgui_title_bar_template()

        _, self.active = imgui.checkbox("active", self.active)
        imgui.same_line()
        if c.icon_text_button('delete-bin-fill', 'delete'):
            delete_self = True
            changed |= True
        imgui.pop_id()

        return changed, delete_self

    def imgui_title_bar_template(self):
        # region TITLE BAR
        if self._imgui_editing_name:
            imgui.push_id(f'{self.name}_name_input')
            _, self._imgui_name_variable = imgui.input_text('', self._imgui_name_variable)
            imgui.pop_id()
            imgui.same_line()
            if imgui.button('confirm'):
                self.name = self._imgui_name_variable
                self._imgui_editing_name = False
            imgui.same_line()
            if imgui.button('cancel'):
                self._imgui_editing_name = False
        else:
            c.bold_text(self.name)
            if imgui.is_mouse_double_clicked(0) and imgui.is_item_hovered():
                self._imgui_editing_name = True
            c.easy_tooltip(f'Double click to rename')
        # endregion

    def is_points_inside(self, points):
        pass


class BaseGeometry3D(BaseGeometry):
    """auto update m_proj m_model m_camera"""

    def __init__(self, name, program_path, vao: Optional[VAO] = None, mode=moderngl.TRIANGLES):
        super().__init__(name)
        if vao is None:
            self.vao: VAO = VAO(name, mode=mode)
        else:
            self.vao: VAO = vao
        self.prog = g.mWindowEvent.load_program(program_path)
        self.ctx = g.mWindowEvent.ctx
        self.vertices = -1
        self.first = 0
        self.instances = 1

        self.parent_rotation = (0., 0., 0.)  # parent rotation in radius
        self.parent_translation = (0., 0., 0.)  # parent transition
        self.rotation = (0., 0., 0.)  # local rotation in radius
        self.translation = (0., 0., 0.)  # local translation
        self.scale = (1., 1., 1.)  # local scale

        self.world_matrix = Matrix44.from_eulers((-math.pi / 2, 0, 0), dtype='f4')

        self.cached_render_camera = None

        self._imgui_translation = (0., 0., 0.)
        self._imgui_rotation = (0., 0., 0.)  # degree
        self._imgui_scale = (1., 1., 1.)

    def before_render(self):
        pass

    @property
    def world_rotation(self):
        """获取世界旋转"""
        return (self.parent_rotation[0] + self.rotation[0],
                self.parent_rotation[1] + self.rotation[1],
                self.parent_rotation[2] + self.rotation[2])

    @property
    def world_translation(self):
        """获取世界平移"""
        return (self.parent_translation[0] + self.translation[0],
                self.parent_translation[1] + self.translation[1],
                self.parent_translation[2] + self.translation[2])

    @property
    def model_view(self):
        rotation = Matrix44.from_eulers(self.world_rotation, dtype='f4')
        translation = Matrix44.from_translation(self.world_translation, dtype='f4')
        scale = Matrix44.from_scale(self.scale, dtype='f4')
        model_view = self.world_matrix * translation * rotation * scale
        return model_view

    @property
    def model_view_with_no_world_matrix(self):
        rotation = Matrix44.from_eulers(self.world_rotation, dtype='f4')
        translation = Matrix44.from_translation(self.world_translation, dtype='f4')
        scale = Matrix44.from_scale(self.scale, dtype='f4')
        model_view = translation * rotation * scale
        return model_view

    def render(self, camera: Camera):
        self.cached_render_camera = camera
        self.prog['m_proj'].write(camera.projection.matrix)
        self.prog['m_model'].write(self.model_view)
        self.prog['m_camera'].write(camera.matrix)
        self.before_render()
        self.vao.render(self.prog, vertices=self.vertices, first=self.first, instances=self.instances)
        self.after_render()

    def after_render(self):
        pass

    @abstractmethod
    def operation_panel(self):
        changed, delete_self = super().operation_panel()
        imgui.push_id(self.uid)
        imgui.separator()
        # region TRANSITION, ROTATION AND SCALE
        transition_changed, self._imgui_translation = imgui.drag_float3(
            'transition', *self._imgui_translation, global_userinfo.get_user_settings('move_scroll_speed'))
        if transition_changed:
            self.translation = self._imgui_translation
            changed |= True

        rotation_changed, self._imgui_rotation = imgui.drag_float3('rotation', *self._imgui_rotation,
                                                                   global_userinfo.get_user_settings('rotate_scroll_speed'))
        if rotation_changed:
            self.rotation = (math.radians(self._imgui_rotation[0]),
                             math.radians(self._imgui_rotation[1]),
                             math.radians(self._imgui_rotation[2]))
            changed |= True

        scale_changed, self._imgui_scale = imgui.drag_float3('scale', *self._imgui_scale,
                                                             global_userinfo.get_user_settings('scale_scroll_speed'), 0.0)
        if scale_changed:
            self.scale = self._imgui_scale
            changed |= True
        imgui.pop_id()
        # endregion
        return changed, delete_self


class PointCloud(BaseGeometry3D):
    def __init__(self, name, pos_arr, color_arr):
        """color_arr should be in range(0, 1)"""
        if color_arr.shape[1] == 3:
            super().__init__(name, program_path='programs/point_cloud_rgb.glsl', mode=moderngl.POINTS)
            self.vao.buffer(pos_arr, '3f', ['in_position'])
            self.vao.buffer(color_arr, '3f', ['in_color'])

        else:
            super().__init__(name, program_path='programs/point_cloud_rgba.glsl', mode=moderngl.POINTS)
            self.vao.buffer(pos_arr, '3f', ['in_position'])
            self.vao.buffer(color_arr, '4f', ['in_color'])

        self.bbox = np.vstack((np.min(pos_arr, axis=0), np.max(pos_arr, axis=0)))

    @abstractmethod
    def operation_panel(self):
        return super().operation_panel()


class Line3D(BaseGeometry3D):
    def __init__(self, points, color=(1, 1, 1, 1), name='line_3d', mode=moderngl.LINES):
        pos_arr = np.array(points, dtype=np.float32)
        if len(color) == 3:
            super().__init__(name, program_path='programs/line_rgb.glsl', mode=mode)
        else:
            super().__init__(name, program_path='programs/line_rgba.glsl', mode=mode)
        self.vao.buffer(pos_arr, '3f', ['in_position'])
        self.prog['color'].value = color
        self.points = points
        self.pos_arr = pos_arr

        self._debug = False

    def operation_panel(self):
        changed, delete_self = super().operation_panel()
        if imgui.button("points to clip space"):
            self._debug = not self._debug
        return changed, delete_self

    def points_to_clip_space(self, camera):
        m_proj = camera.projection.matrix
        m_model = self.model_view
        m_camera = camera.matrix
        full_matrix = np.array(m_proj * m_camera * m_model)

        # 将点云坐标扩展到齐次坐标系
        homogeneous_points = np.c_[self.points, np.ones((self.points.shape[0], 1))]

        # 使用逆矩阵 inverse_model_view 进行逆变换
        transformed_points = np.dot(homogeneous_points, full_matrix)

        # 将变换后的点坐标恢复至三维坐标
        restored_points = transformed_points[:, :3] / transformed_points[:, 3].reshape(-1, 1)
        print(restored_points[0])

        # 右边是1 左边-1 上面-1 下面1

    def after_render(self):
        if self.cached_render_camera is None:
            return
        if self._debug:
            self.points_to_clip_space(self.cached_render_camera)


class WiredBoundingBox(Line3D):
    def __init__(self, name, bound_min, bound_max, color=(1.0, 1.0, 1.0, 1.0)):
        edges = self.generate_edges(bound_min, bound_max)
        super().__init__(points=edges, color=color, name=name, mode=moderngl.LINES)
        self.bound_min = bound_min
        self.bound_max = bound_max
        self.color = color

    def generate_edges(self, bound_min, bound_max):
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
        self.__init__(self.name, bound_min, self.bound_max, self.color)

    def set_bound_max(self, bound_max):
        self.__init__(self.name, self.bound_min, bound_max, self.color)

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
        model_view = torch.tensor(self.model_view_with_no_world_matrix).cuda()
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


class Polygon(Line3D):
    def __init__(self, name, points: np.ndarray, color=(1.0, 1.0, 1.0, 1.0), closed=True):
        # points = (n, 3)
        assert len(points.shape) == 2
        assert points.shape[1] == 3  # 三维点
        if closed:
            points = np.vstack((points, points[0]))
        super().__init__(name=name, points=points, color=color, mode=moderngl.LINE_STRIP)

    def is_points_inside(self, points):
        import torch
        if not isinstance(points, torch.Tensor):
            points = torch.tensor(points)
        if not points.is_cuda:
            points = points.cuda()
        if len(points.shape) == 1:
            points = points.reshape(1, -1)
        assert len(points.shape) == 2
        model_view = torch.tensor(self.model_view_with_no_world_matrix).cuda()
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


class Axis3D(BaseGeometry):
    def __init__(self, name='axis3d'):
        super().__init__(name)
        self.axis_x = Line3D(points=((0, 0, 0), (100, 0, 0)), color=(1, 0, 0, 1))
        self.axis_y = Line3D(points=((0, 0, 0), (0, 100, 0)), color=(0, 1, 0, 1))
        self.axis_z = Line3D(points=((0, 0, 0), (0, 0, 100)), color=(0, 0, 1, 1))

    def render(self, camera: Camera):
        self.axis_x.render(camera)
        self.axis_y.render(camera)
        self.axis_z.render(camera)

    @abstractmethod
    def operation_panel(self):
        imgui.text("nothing to show")
        return False, False


class SimpleCube(BaseGeometry3D):
    def __init__(self, name, size=(1, 1, 1), color=(1.0, 1.0, 1.0, 1.0)):
        super().__init__(name, program_path='programs/cube_simple.glsl', vao=geometry.cube(size))
        self.prog['color'].value = color
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
        model_view = torch.tensor(self.model_view_with_no_world_matrix).cuda()
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


class CubeInstance(BaseGeometry3D):
    def __init__(self):
        super().__init__('cube_instance', program_path='programs/cube_simple_instanced.glsl',
                         vao=geometry.cube(size=(2, 2, 2)))
        # Generate per instance data representing a grid of cubes
        N = 100
        self.instances = N * N

        def gen_data(x_res, z_res, spacing=2.5):
            """Generates a grid of N * N positions and random colors on the xz plane"""
            for y in range(z_res):
                for x in range(x_res):
                    yield -N * spacing / 2 + spacing * x
                    yield 0
                    yield -N * spacing / 2 + spacing * y
                    yield np.random.uniform(0, 1)
                    yield np.random.uniform(0, 1)
                    yield np.random.uniform(0, 1)

        self.instance_data = self.ctx.buffer(np.fromiter(gen_data(N, N), 'f4', count=self.instances * 6))
        self.vao.buffer(self.instance_data, '3f 3f/i', ['in_offset', 'in_color'])

    def before_render(self):
        self.prog['time'].value = g.mTime

    @abstractmethod
    def operation_panel(self):
        return super().operation_panel()


class Polygon3D(BaseGeometry3D):
    def __init__(self, name, points: np.ndarray, z_min, z_max, color=(1.0, 1.0, 1.0, 0.5), closed=True):
        assert len(points.shape) == 2
        assert points.shape[1] == 3  # 三维点
        assert z_max > z_min
        super().__init__(name, program_path='programs/line_rgba.glsl', mode=moderngl.TRIANGLES)
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
        self.vao.buffer(vertices, '3f', ['in_position'])
        self.prog['color'].value = color

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
        model_view = torch.tensor(self.model_view_with_no_world_matrix).cuda()
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
    def __init__(self, name, program_path):
        super().__init__(name)

        self.vao: VAO = geometry.quad_fs()
        self.prog = g.mWindowEvent.load_program(program_path)
        self.ctx = g.mWindowEvent.ctx

    def render(self, camera: None):
        _ = camera
        self.vao.render(self.prog)

    @abstractmethod
    def operation_panel(self):
        return super().operation_panel()


class GaussianPointCloud(BaseGeometry):
    """包裹了一个gaussian manager 和 PointCloud的geometry"""

    def __init__(self, name, gaussian_manager=None, debug_collection=None):
        super().__init__(name)
        # 维护的对象
        # 1. gaussian manager
        from src.manager.gaussian_manager import GaussianManager
        self.gm: Optional[GaussianManager] = gaussian_manager
        from gui.contents import ViewerContent
        self.ViewerContentClass = ViewerContent
        # 2. gaussian point cloud
        self.gaussian_point_cloud: Optional[PointCloud] = None

        # debug collection
        from gui.graphic.geometry_collection import DebugCollection
        self.debug_collection: Optional[DebugCollection] = debug_collection  # 用于显示各种debug信息
        # 3. debug bbox
        self.debug_bbox: Optional[WiredBoundingBox] = None

        # 几何变换等信息
        self.transition = np.zeros((3,), dtype=np.float32)
        self.rotation = np.zeros((3,), dtype=np.float32)
        # 其他信息
        self._imgui_transition = (0, 0, 0)
        self._imgui_rotation = (0, 0, 0)  # degree
        self._imgui_show_debug_bbox = True  # 显示bbox

        # 缓存信息
        pass

    def update_debug_geometries_matrix_model(self):
        """当self的位置和旋转改变时， 更新对应的debug geometries的位置和旋转"""
        self.debug_bbox.parent_translation = self.transition
        self.debug_bbox.parent_rotation = self.rotation

    def update_gaussian_points_matrix_model(self):
        """当自身的位置和旋转改变时， 更新对应的point cloud的位置和旋转"""
        self.gaussian_point_cloud.translation = self.transition
        self.gaussian_point_cloud.rotation = self.rotation

    def generate_gaussian_points(self):
        """根据gm中的gaussians的点云数据更新自身的PointCloud"""
        if self.gm is None:
            logging.warning('no gaussian manger')
            return
        # 重置变换信息
        self.transition = np.zeros((3,), dtype=np.float32)
        self.rotation = np.zeros((3,), dtype=np.float32)  # rad
        self._imgui_transition = (0, 0, 0)
        self._imgui_rotation = (0, 0, 0)  # degree

        # 根据现在gaussian manager中的点重新创建point cloud
        logging.info(f'updating gaussian points')
        pos_arr = self.gm.gaussians.get_xyz.detach().cpu().numpy()  # (n, 3)
        rgb_arr = self.gm.gaussians.get_features_dc.detach().cpu().numpy().squeeze(axis=1)  # (n, 3)
        alpha_arr = self.gm.gaussians.get_alpha.detach().cpu().numpy().squeeze(axis=1)
        rgba = np.hstack((rgb_arr, alpha_arr.reshape(-1, 1)))
        SH_C0 = 0.28209479177387814
        rgba[:, 0:3] = (0.5 + SH_C0 * rgba[:, 0:3])
        rgba[:, 3] = (1 / (1 + np.exp(-rgba[:, 3])))
        rgba = np.clip(rgba, 0.0, 1.0)
        self.gaussian_point_cloud = PointCloud(f'{self.name}_point_cloud', pos_arr, rgba)
        # 更新其他debug geometries
        # bbox被重新生成
        bbox = self.gaussian_point_cloud.bbox
        self.debug_bbox = WiredBoundingBox(f'{self.name}_bbox', bbox[0], bbox[1])

    def show_debug_info(self):
        c.bold_text(f'[{self.__class__.__name__}(class)]')

    def operation_panel(self, is_the_only_geo=False) -> tuple:

        """
        高斯几何体的操作面板
        return (changed, delete_self)
        """
        # region outputs
        delete_self = False  # to tell the parent collection to delete self
        changed = False
        # endregion

        imgui.push_id(self.uid)
        # region 标题栏、删除按钮
        self.imgui_title_bar_template()
        if c.icon_text_button('delete-bin-fill', 'Delete Gaussian', uid=f"delete gaussian button {self.uid}"):
            delete_self = True
            changed |= True
        # endregion
        # region 更新GAUSSIAN POINTS
        if imgui.button('Update Gaussian Points'):
            self.generate_gaussian_points()
            changed |= True
        c.easy_tooltip('Manually update gaussian points base on GaussianManager.gaussians')
        # endregion
        imgui.separator()
        # region GAUSSIAN MANAGER STUFF, TRANSITION, ROTATION AND OTHERS
        if imgui.button("cache"):
            self.gm.cache()

        if self.gm.gaussians_backup is not None:
            imgui.same_line()
            if imgui.button("restore"):
                self.gm.restore()
            imgui.same_line()
            if imgui.button("apply"):
                self.gm.apply()
        else:
            StyleModule.push_disabled_button_color()
            imgui.same_line()
            imgui.button("restore")
            imgui.same_line()
            imgui.button("apply")
            StyleModule.pop_button_color()

        transition_changed, self._imgui_transition = imgui.drag_float3(
            'transition', *self._imgui_transition, global_userinfo.get_user_settings('move_scroll_speed'))
        if imgui.is_item_deactivated_after_edit() or (is_the_only_geo and transition_changed):
            offset = np.array(self._imgui_transition, dtype=np.float32) - self.transition
            self.gm.move(offset)
            self.transition = np.array(self._imgui_transition, dtype=np.float32)
            changed |= True

        rotation_changed, self._imgui_rotation = imgui.drag_float3('rotation', *self._imgui_rotation, 1.0)
        if imgui.is_item_deactivated_after_edit() or (is_the_only_geo and rotation_changed):
            org_rotation_matrix = Matrix44.from_eulers(self.rotation)
            new_rotation_matrix = Matrix44.from_eulers(np.array(self._imgui_rotation) * math.pi / 180)
            rotation_matrix = new_rotation_matrix @ org_rotation_matrix.inverse
            self.gm.rotate(rotation_matrix)
            self.rotation = np.array(self._imgui_rotation, dtype=np.float32) / 180.0 * math.pi  # convert to rad
            changed |= True
        if changed:
            self.update_gaussian_points_matrix_model()
            self.update_debug_geometries_matrix_model()
        # endregion

        imgui.pop_id()

        # debug collection
        if self.debug_collection is not None:
            if self._imgui_show_debug_bbox:
                self.debug_collection.draw_bbox(self.debug_bbox, skip_examine=True)

        return changed, delete_self

    def render(self, camera: Camera):
        self.gaussian_point_cloud.render(camera)
