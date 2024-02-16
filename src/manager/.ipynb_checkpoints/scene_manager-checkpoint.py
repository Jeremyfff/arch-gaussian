import math
import sys

sys.path.append("./src")
import open3d as o3d
from utils.graphics_utils import getWorld2View2, tr2pa, pa2tr
import numpy as np
from scipy.spatial.transform import Rotation as R
from scene.gaussian_model import BasicPointCloud


class SceneManager:
    def __init__(self, scene_info):
        self.__scene_info = scene_info
        self.__cached_cam_pos = None
        self.__cached_cam_axis = None
        self.__cached_ground_up_vec = None

    def get_cam_pos_and_axis(self):
        _cam_pos_list = []
        _cam_axis_list = []

        for i in range(len(self.__scene_info.train_cameras)):
            cam = self.__scene_info.train_cameras[i]
            pos, axis = tr2pa(cam.T, cam.R)
            _cam_pos_list.append(pos)
            _cam_axis_list.append(axis)
        _cam_pos_array = np.array(_cam_pos_list)
        _cam_axis_array = np.array(_cam_axis_list)
        self.__cached_cam_pos = _cam_pos_array
        self.__cached_cam_axis = _cam_axis_array
        return _cam_pos_array, _cam_axis_array

    @staticmethod
    def __normalize_vec(_vec):
        norm = np.linalg.norm(_vec)
        return _vec / norm

    def get_ground_up_vec(self):
        if self.__cached_cam_axis is None:
            self.get_cam_pos_and_axis()  # this step will add cam_axis to cache
        assert self.__cached_cam_axis is not None, "self.cached_cam_axis is None"
        # ground up vector
        randomly_selected_cam_rs = self.__cached_cam_axis[
            np.random.choice(self.__cached_cam_axis.shape[0], self.__cached_cam_axis.shape[0] // 3 * 2, replace=False)]
        np.random.shuffle(randomly_selected_cam_rs)
        half_size = len(randomly_selected_cam_rs) // 2
        group1 = randomly_selected_cam_rs[:half_size]
        group2 = randomly_selected_cam_rs[half_size:]
        ups = []
        for j in range(len(group1)):
            vec1 = self.__normalize_vec(group1[j][0])
            vec2 = self.__normalize_vec(group2[j][0])
            dis_sq = np.dot((vec1 - vec2) , (vec1 - vec2))
            if dis_sq < 0.1:
                continue
            up = self.__normalize_vec(np.cross(vec1, vec2))
            if len(ups) > 0 and np.dot(ups[0], up) < 0.0:
                up *= -1
            ups.append(up)
        ups = np.array(ups)
        mean_up = ups.mean(axis=0)
        mean_cam_pos = self.__cached_cam_pos.mean(axis=0)
        mean_pos = self.__scene_info.point_cloud.points.mean(axis=0)
        if np.dot(mean_up, mean_cam_pos - mean_pos) < 0:
            # reverse up vector
            mean_up *= -1
        self.__cached_ground_up_vec = mean_up
        return mean_up

    def visualize(self, draw_axis=True, draw_cameras=True,vis=True ):
        # W2C
        # | CAM.R.transpose()     CAM.T |
        # |  0                      1   |
        # C2W = np.linalg.inv(W2C)
        # C2W
        # |cam_axis.transpose()  cam pos |
        # |        0                1    |

        # prepare
        if self.__cached_cam_axis is None or self.__cached_cam_pos is None:
            print("getting cam pos and axis")
            self.get_cam_pos_and_axis()  # this step will add cam_axis to cache
        assert self.__cached_cam_axis is not None and self.__cached_cam_pos is not None, \
            "self.cached_cam_axis or self.cached_cam_pos is None"
        if self.__cached_ground_up_vec is None:
            print("getting ground up vector")
            self.get_ground_up_vec()
        assert self.__cached_ground_up_vec is not None, "self.cached_ground_up_vec is None"
        geometries = []

        point_cloud = o3d.geometry.PointCloud()
        point_cloud.points = o3d.utility.Vector3dVector(self.__scene_info.point_cloud.points)
        point_cloud.colors = o3d.utility.Vector3dVector(self.__scene_info.point_cloud.colors)
        geometries.append(point_cloud)

        if draw_axis:
            # 创建numpy数组表示三条线段的起点和终点
            start_points = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
            end_points = np.array([[100, 0, 0], [0, 100, 0], [0, 0, 100]])
            # 创建LineSet对象
            axis_lines = o3d.geometry.LineSet()
            axis_lines.points = o3d.utility.Vector3dVector(np.concatenate([start_points, end_points], axis=0))
            axis_lines.lines = o3d.utility.Vector2iVector(np.array([[0, 3], [1, 4], [2, 5]]))
            axis_lines.colors = o3d.utility.Vector3dVector(
                np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]).astype(np.float32))
            geometries.append(axis_lines)

        if draw_cameras:
            # points
            cam_point_cloud = o3d.geometry.PointCloud()
            cam_point_cloud.points = o3d.utility.Vector3dVector(self.__cached_cam_pos)
            cam_point_cloud.colors = o3d.utility.Vector3dVector(
                np.tile(np.array([1, 0, 0]), (self.__cached_cam_pos.shape[0], 1)))

            # lines
            cam_line_start = np.expand_dims(self.__cached_cam_pos, axis=1)
            cam_line_start = np.tile(cam_line_start, (1, 3, 1))
            cam_line_scale = 1.0
            cam_line_end = cam_line_start + self.__cached_cam_axis * cam_line_scale

            cam_line_start = cam_line_start.reshape(-1, 3)
            cam_line_end = cam_line_end.reshape(-1, 3)

            num_lines = cam_line_start.shape[0]
            cam_line_points = np.concatenate((cam_line_start, cam_line_end), axis=0)

            first_column = np.arange(num_lines)
            cam_line_lines = np.stack([first_column, first_column + num_lines], axis=1)

            cam_line_colors = np.tile(np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]), ((num_lines + 2) // 3, 1))[
                              :num_lines]

            cam_lines = o3d.geometry.LineSet()
            cam_lines.points = o3d.utility.Vector3dVector(cam_line_points)
            cam_lines.lines = o3d.utility.Vector2iVector(cam_line_lines)
            cam_lines.colors = o3d.utility.Vector3dVector(cam_line_colors)

            geometries.append(cam_point_cloud)
            geometries.append(cam_lines)

            # ground up vector

            up_lines = o3d.geometry.LineSet()
            up_lines.points = o3d.utility.Vector3dVector(np.array([[0, 0, 0], self.__cached_ground_up_vec * 200]))
            up_lines.lines = o3d.utility.Vector2iVector(np.array([[0, 1]]))
            up_lines.colors = o3d.utility.Vector3dVector(np.array([[0.5, 0, 0.5]]))
            geometries.append(up_lines)

        if vis:
            o3d.visualization.draw_geometries(geometries)

    def rotate(self, rotation:R) -> 'SceneManager':
        rotated_points = rotation.apply(self.__scene_info.point_cloud.points).astype(np.float32)

        pcd = BasicPointCloud(points=rotated_points, colors=self.__scene_info.point_cloud.colors,
                              normals=self.__scene_info.point_cloud.normals)

        rotated_cameras = []
        for i in range(len(self.__scene_info.train_cameras)):
            cam = self.__scene_info.train_cameras[i]
            cam_pos, cam_axis = tr2pa(cam.T, cam.R)

            new_cam_pos = rotation.apply(cam_pos).astype(np.float32)
            new_cam_axis = rotation.apply(cam_axis).astype(np.float32)

            new_cam_t, new_cam_r = pa2tr(new_cam_pos, new_cam_axis)
            rotated_cameras.append(cam._replace(R=new_cam_r, T=new_cam_t))

        new_scene_info = self.__scene_info._replace(point_cloud=pcd, train_cameras=rotated_cameras)

        return SceneManager(new_scene_info)


    def fix(self) -> 'SceneManager':
        if self.__cached_cam_axis is None or self.__cached_cam_pos is None:
            self.get_cam_pos_and_axis()  # this step will add cam_axis to cache
        assert self.__cached_cam_axis is not None and self.__cached_cam_pos is not None, \
            "self.cached_cam_axis or self.cached_cam_pos is None"
        if self.__cached_ground_up_vec is None:
            self.get_ground_up_vec()
        assert self.__cached_ground_up_vec is not None, "self.cached_ground_up_vec is None"
        print(f"org up {self.__cached_ground_up_vec}")
        z_axis = np.array([0, 0, 1])
        rotation = R.align_vectors(self.__cached_ground_up_vec.reshape((1, 3)), z_axis.reshape((1, 3)))[0]
        print(rotation.as_euler('XYZ')*180/math.pi)
        tmp = self.rotate(rotation)
        print(f"new up {tmp.get_ground_up_vec()}")
        return tmp

    def clear_cache(self):
        self.__cached_cam_pos = None
        self.__cached_cam_axis = None
        self.__cached_ground_up_vec = None

    def get_scene_info(self):
        return self.__scene_info
