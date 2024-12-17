import random

from scene.cameras import Camera
from scene.dataset_readers import CameraInfo
from utils.camera_utils import cameraList_from_camInfos


class CameraManager:
    def __init__(self):
        self.train_cameras: dict[float: list[Camera]] = {}
        self.test_cameras: dict[float: list[Camera]] = {}
        self.default_resolution_scale: float = 1.0
        self.resolution_scales: list[float] = [self.default_resolution_scale]
        self.sorted_cameras: dict[float: list[Camera]] = {}

    def create_cameras(self, args, scene_info):
        """
        @Jeremy
        create cameras from scene info
        """

        print("Creating Cameras")
        self.train_cameras = {}
        self.test_cameras = {}
        shuffle = True
        if shuffle:
            random.shuffle(scene_info.train_cameras)  # Multi-res consistent random shuffling
            random.shuffle(scene_info.test_cameras)  # Multi-res consistent random shuffling

        for resolution_scale in self.resolution_scales:
            print("Loading Training Cameras")
            self.train_cameras[resolution_scale] = cameraList_from_camInfos(scene_info.train_cameras, resolution_scale,
                                                                            args)
            if args.eval:
                print("Loading Test Cameras")
                self.test_cameras[resolution_scale] = cameraList_from_camInfos(scene_info.test_cameras,
                                                                               resolution_scale, args)

            cam_name_dict = {}
            for cam in self.train_cameras[resolution_scale]:
                cam_name_dict[cam.image_name] = cam
            sorted_dict = {k: cam_name_dict[k] for k in sorted(cam_name_dict)}
            self.sorted_cameras[resolution_scale] = list(sorted_dict.values())

        print("😀Complete.")
        return self.train_cameras, self.test_cameras

    def pick_camera(self, index: int, resolution_scale=1.0) -> Camera:
        assert self.train_cameras != {}, "no camera loaded"
        assert self.sorted_cameras != {}
        return self.sorted_cameras[resolution_scale][index]

    def remove_last_camera(self):
        for resolution_scale in self.sorted_cameras:
            self.sorted_cameras[resolution_scale].pop()
        for resolution_scale in self.train_cameras:
            self.train_cameras[resolution_scale].pop()
