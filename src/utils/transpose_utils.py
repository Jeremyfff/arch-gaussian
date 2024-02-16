import random
from enum import Enum
from utils.camera_utils import loadCam
import numpy as np
import torch
from scipy.spatial.transform import Rotation as R

class MatrixFormat(Enum):
    numpy = 1
    torch = 2

class TransposeHelper():
    def __init__(self, args, scene_info):
        self.args = args
        self.scene_info = scene_info
        self.cached_cams = {}
        self.cached_mean_ground_up_vector = None
        self.cached_rotation_matrix = None
        self.cached_rotation = None
    def __get_cam(self, cam_index, cache=True):
        if cam_index in self.cached_cams.keys():
            cam = self.cached_cams[cam_index]
        else:
            cam_info = self.scene_info.train_cameras[cam_index]
            cam = loadCam(args=self.args, id=cam_index, cam_info=cam_info, resolution_scale=1)
            if cache:
                self.cached_cams[cam_index] = cam
        return cam

    def __get_ground_up_vector(self, cam1_index, cam2_index, reverse=False, cache=True):
        axis = 0
        cam1 = self.__get_cam(cam1_index, cache=cache)
        right_vector1 = cam1.R[:, axis]

        cam2 = self.__get_cam(cam2_index, cache=cache)
        right_vector2 = cam2.R[:, axis]

        ground_up_vector = np.cross(right_vector1, right_vector2)
        normalized_ground_up_vector = ground_up_vector / np.linalg.norm(ground_up_vector)
        if reverse:
            normalized_ground_up_vector *= -1
        return normalized_ground_up_vector

    def get_ground_up_vector_auto(self, reverse=False, sample_count=10, cache=True):
        print(f'sample count = {sample_count}')
        assert sample_count > 0, "sample count must > 0"
        if self.cached_mean_ground_up_vector:
            print("use cached mean ground up vector")
            return self.cached_mean_ground_up_vector
        normalized_ground_up_vectors = []
        normalized_ground_up_vector_first = self.__get_ground_up_vector(0, 2, reverse, cache)
        normalized_ground_up_vectors.append(normalized_ground_up_vector_first)
        for i in range(sample_count):
            normalized_ground_up_vector = self.__get_ground_up_vector(0, random.randint(1,
                                                                                        len(self.scene_info.train_cameras)-1),
                                                                      reverse, cache)
            if np.dot(normalized_ground_up_vector_first, normalized_ground_up_vector) < 0:
                normalized_ground_up_vector *= -1
            normalized_ground_up_vectors.append(normalized_ground_up_vector)
        normalized_ground_up_vectors = np.array(normalized_ground_up_vectors)
        print(normalized_ground_up_vectors)
        mean_ground_up_vector = np.mean(normalized_ground_up_vectors, axis=0)
        if cache:
            self.cached_mean_ground_up_vector = mean_ground_up_vector
        return mean_ground_up_vector

    @staticmethod
    def rotation_from_vectors(vec1:np.ndarray, vec2:np.ndarray) -> R:
        vec1 = vec1.reshape(1, 3)
        vec2 = vec2.reshape(1, 3)
        rotation = R.align_vectors(vec1, vec2)[0]
        return rotation

    @staticmethod
    def rotation_matrix_from_vectors_legacy(vec1, vec2):
        # 单位化向量
        vec1 = vec1 / np.linalg.norm(vec1)
        vec2 = vec2 / np.linalg.norm(vec2)

        # 计算旋转轴
        axis = np.cross(vec1, vec2)
        axis = axis / np.linalg.norm(axis)

        # 计算旋转角度
        angle = np.arccos(np.dot(vec1, vec2))

        # 计算旋转矩阵
        rotation_matrix = np.array([
            [np.cos(angle) + axis[0] ** 2 * (1 - np.cos(angle)),
             axis[0] * axis[1] * (1 - np.cos(angle)) - axis[2] * np.sin(angle),
             axis[0] * axis[2] * (1 - np.cos(angle)) + axis[1] * np.sin(angle)],
            [axis[1] * axis[0] * (1 - np.cos(angle)) + axis[2] * np.sin(angle),
             np.cos(angle) + axis[1] ** 2 * (1 - np.cos(angle)),
             axis[1] * axis[2] * (1 - np.cos(angle)) - axis[0] * np.sin(angle)],
            [axis[2] * axis[0] * (1 - np.cos(angle)) - axis[1] * np.sin(angle),
             axis[2] * axis[1] * (1 - np.cos(angle)) + axis[0] * np.sin(angle),
             np.cos(angle) + axis[2] ** 2 * (1 - np.cos(angle))]
        ]).astype(np.float32)

        return rotation_matrix


    def get_calibration_rotation(self, cache=True):
        """
           Get the calibration rotation based on the cached mean ground up vector and
           the default up vector [0, 0, 1].

           Returns:
               Rotation: The computed or cached calibration rotation.
           """
        if self.cached_rotation is not None:
            return self.cached_rotation
        up_vector = np.array([0, 0, 1])
        ground_up_vector = self.cached_mean_ground_up_vector
        assert ground_up_vector is not None, "必须先计算地面法线向量 get_ground_up_vector_auto"
        rotation = self.rotation_from_vectors(up_vector, ground_up_vector)
        if cache:
            self.cached_rotation = rotation
        return rotation


    def get_rotation_matrix_legacy(self, ground_up_vector=None, cache=True, matrix_format:MatrixFormat=MatrixFormat.numpy):
        if self.cached_rotation_matrix is not None:
            if matrix_format == MatrixFormat.numpy:
                print("use cached rotation matrix (numpy.ndarray)")
                return self.cached_rotation_matrix
            elif matrix_format == MatrixFormat.torch:
                print("use cached rotation matrix (torch.tensor)")
                return torch.tensor(self.cached_rotation_matrix)
            print("use cached rotation matrix (numpy.ndarray)")
            return self.cached_rotation_matrix
        up_vector = np.array([0, 0, 1])
        if ground_up_vector is None:
            ground_up_vector = self.cached_mean_ground_up_vector
        assert ground_up_vector is not None, "必须有一个地面法线向量"
        rotation_matrix = self.rotation_matrix_from_vectors(ground_up_vector, up_vector)
        if cache:
            self.cached_rotation_matrix = rotation_matrix
        if matrix_format == MatrixFormat.numpy:
            return rotation_matrix
        elif matrix_format == MatrixFormat.torch:
            return torch.tensor(rotation_matrix)
        return rotation_matrix



    def clear_all_cache(self):

        self.cached_cams = {}
        self.cached_mean_ground_up_vector = None
        self.cached_rotation_matrix = None

    def create_new_func(self):
        print("new func")

