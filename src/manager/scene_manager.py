import math
import pickle
import sys

from scene import sceneLoadTypeCallbacks
from scene.dataset_readers import SceneInfo

sys.path.append("./src")
import open3d as o3d
from utils.graphics_utils import getWorld2View2, tr2pa, pa2tr
import numpy as np
from scipy.spatial.transform import Rotation as R
from scene.gaussian_model import BasicPointCloud
import os


class SceneManager:
    """
    @Jeremy
    """

    def __init__(self, scene_info):
        # scene info
        self.__scene_info = scene_info
        # caches
        self.__cached_cam_pos = None
        self.__cached_cam_axis = None
        self.__cached_ground_up_vec = None

    def get_cam_pos_and_axis(self) -> tuple[np.ndarray, np.ndarray]:
        """
        @Jeremy
        Calculate camera position and axis,
        store then in __cached_cam_pos and __cached_cam_axis
        """
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
    def __normalize_vec(_vec: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(_vec)
        return _vec / norm

    def get_ground_up_vec(self) -> np.ndarray:
        """
        @Jeremy
        Calculate the average ground upward vector
        by calculating several pairs of camera axes and averaging them.
        Get cached ground up vector if __cached_cam_axis is not None,
        else, calculate a new ground up vector
        """
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
            dis_sq = np.dot((vec1 - vec2), (vec1 - vec2))
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

    def visualize(self, draw_axis=True, draw_cameras=True, vis=True) -> None:
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

    def rotate(self, rotation: R) -> 'SceneManager':
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

    def fix(self, cached_rotation=None) -> ('SceneManager', R):
        if cached_rotation is not None:
            print("use cached rotation")
            return self.rotate(cached_rotation), cached_rotation
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
        rotation = rotation.inv()
        print(rotation.as_euler('XYZ') * 180 / math.pi)
        return self.rotate(rotation), rotation

    def clear_cache(self) -> None:
        self.__cached_cam_pos = None
        self.__cached_cam_axis = None
        self.__cached_ground_up_vec = None

    def get_scene_info(self) -> SceneInfo:
        return self.__scene_info


def load_and_fix_scene(args) -> SceneInfo:
    """
    @Jeremy
    一个从args快速创教场景并修复的便捷工具
    该方法对SceneManager进行了高级包装
    当运行该方法时， 会进行以下操作：
    从磁盘加载场景信息并创建一个sceneManager对象，使用该sceneManager对象的修复工具修复场景，得到新的SceneInfo
    如果检测到磁盘上的args.source_path路径下的cache文件夹内存在rotation.bin缓存文件，则直接使用rotation.bin中包含的旋转进行旋转，
    该步操作是由于每次fix的平均地面向上向量都会有微小差别，使用缓存文件能够保证每次旋转得到的场景完全一致
    修复的场景文件是一个new_scene_manager
    最终返回该new_scene_manager的scene_info
    """
    print("😀creating scene info from Colmap sparse")
    if os.path.exists(os.path.join(args.source_path, "sparse")):
        scene_info = sceneLoadTypeCallbacks["Colmap"](args.source_path, args.images, args.eval)
    else:
        assert False, "Could not recognize scene type!"
    assert len(scene_info.test_cameras) == 0, "args.eval must be False"

    print("🔧fixing scene...")
    scene_manager = SceneManager(scene_info)
    cached_rotation_path = os.path.join(args.source_path, "cache", "rotation.bin")

    if os.path.exists(cached_rotation_path):
        # 有缓存文件的情况
        with open(cached_rotation_path, 'rb') as f:
            cached_rotation = pickle.load(f)
        new_scene_manager, rotation = scene_manager.fix(cached_rotation=cached_rotation)
    else:
        # 没有缓存文件的情况
        new_scene_manager, rotation = scene_manager.fix()

        # 缓存生成的文件
        os.makedirs(os.path.dirname(cached_rotation_path), exist_ok=True)
        with open(cached_rotation_path, "wb") as f:
            pickle.dump(rotation, f)
        print(f"📝fix rotation cached to {cached_rotation_path}")
    assert new_scene_manager is not None, "scene fix failed"
    new_up_vec = new_scene_manager.get_ground_up_vec()
    print(f"🔍fixed up vector: {new_up_vec}")
    assert new_up_vec[2] > 0.85, "修复失败，请手动排查"
    # new_scene_manager.visualize()  # 可视化
    print(f"😊fix complete\n")

    scene_info = new_scene_manager.get_scene_info()
    print("========== scene info ===========")
    print(f"train cams count: {len(scene_info.train_cameras)}")
    print(f"test cams count: {len(scene_info.test_cameras)}")
    print(f"points count: {scene_info.point_cloud.points.shape[0]}")
    print("================================")
    return scene_info
