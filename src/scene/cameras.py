#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

import torch
from torch import nn
import numpy as np
from utils.graphics_utils import getWorld2View2, getProjectionMatrix, tr2pa, pa2tr, pa2cw
from scipy.spatial.transform import Rotation as R


class Camera(nn.Module):
    def __init__(self, colmap_id, R, T, FoVx, FoVy, image, gt_alpha_mask,
                 image_name, uid,
                 trans=np.array([0.0, 0.0, 0.0]), scale=1.0, data_device="cuda"
                 ):
        super(Camera, self).__init__()

        self.uid = uid
        self.colmap_id = colmap_id
        self.R = R
        self.T = T
        self.FoVx = FoVx
        self.FoVy = FoVy
        self.image_name = image_name

        try:
            self.data_device = torch.device(data_device)
        except Exception as e:
            print(e)
            print(f"[Warning] Custom device {data_device} failed, fallback to default cuda device")
            self.data_device = torch.device("cuda")

        self.original_image = image.clamp(0.0, 1.0).to(self.data_device)
        self.image_width = self.original_image.shape[2]
        self.image_height = self.original_image.shape[1]

        if gt_alpha_mask is not None:
            self.original_image *= gt_alpha_mask.to(self.data_device)
        else:
            self.original_image *= torch.ones((1, self.image_height, self.image_width), device=self.data_device)

        self.zfar = 100.0
        self.znear = 0.01

        self.trans = trans
        self.scale = scale

        self.world_view_transform = torch.tensor(getWorld2View2(R, T, trans, scale)).transpose(0, 1).cuda()
        self.projection_matrix = getProjectionMatrix(znear=self.znear, zfar=self.zfar, fovX=self.FoVx,
                                                     fovY=self.FoVy).transpose(0, 1).cuda()
        self.full_proj_transform = (
            self.world_view_transform.unsqueeze(0).bmm(self.projection_matrix.unsqueeze(0))).squeeze(0)
        self.camera_center = self.world_view_transform.inverse()[3, :3]


    def update(self):
        self.world_view_transform = torch.tensor(getWorld2View2(self.R, self.T, self.trans, self.scale)).transpose(0, 1).cuda()
        self.projection_matrix = getProjectionMatrix(znear=self.znear, zfar=self.zfar, fovX=self.FoVx,
                                                     fovY=self.FoVy).transpose(0, 1).cuda()
        self.full_proj_transform = (
            self.world_view_transform.unsqueeze(0).bmm(self.projection_matrix.unsqueeze(0))).squeeze(0)
        self.camera_center = self.world_view_transform.inverse()[3, :3]

class MiniCam:
    def __init__(self, T, R, width, height, fovy, fovx, znear=0.01, zfar=100.0):
        # c2w (pose) should be in NeRF convention.
        self.T = T
        self.R = R
        self.image_width = width
        self.image_height = height
        self.FoVy = fovy
        self.FoVx = fovx
        self.znear = znear
        self.zfar = zfar
        self.trans = np.array([0.0, 0.0, 0.0])
        self.scale = 1.0

        self.world_view_transform = torch.tensor(getWorld2View2(self.R, self.T, self.trans, self.scale)).transpose(0,
                                                                                                                   1).cuda()
        self.projection_matrix = getProjectionMatrix(znear=self.znear, zfar=self.zfar, fovX=self.FoVx,
                                                     fovY=self.FoVy).transpose(0, 1).cuda()
        self.full_proj_transform = (
            self.world_view_transform.unsqueeze(0).bmm(self.projection_matrix.unsqueeze(0))).squeeze(0)
        self.camera_center = self.world_view_transform.inverse()[3, :3]

    def load_from_cam(self, cam:Camera):
        self.T = cam.T
        self.R = cam.R
        self.image_width = cam.image_width
        self.image_height = cam.image_height
        self.FoVx = cam.FoVx
        self.FoVy = cam.FoVy
        self.znear = cam.znear
        self.zfar = cam.zfar

        self.update()


    def set_transform(self, pos, euler):
        axis = R.from_euler('XYZ',euler, degrees=True).as_matrix().transpose()
        self.T, self.R = pa2tr(pos, axis)
        # self.update()

    def get_transform(self):
        pos, axis = tr2pa(self.T, self.R)
        euler = R.from_matrix(axis.transpose()).as_euler('XYZ', degrees=True)
        return pos, euler


    def rotate_worldly(self, euler):
        rotation = R.from_euler('XYZ', euler)
        pos, axis = tr2pa(self.T, self.R)
        axis = rotation.apply(axis)
        self.T, self.R = pa2tr(pos, axis)
        # self.update()

    def move_locally(self, vec):
        pos, axis = tr2pa(self.T, self.R)
        pos += np.dot(vec, axis)
        self.T, self.R = pa2tr(pos, axis)
        # self.update()


    def update(self):
        self.world_view_transform = torch.tensor(getWorld2View2(self.R, self.T, self.trans, self.scale)).transpose(0,
                                                                                                                   1).cuda()
        self.projection_matrix = getProjectionMatrix(znear=self.znear, zfar=self.zfar, fovX=self.FoVx,
                                                     fovY=self.FoVy).transpose(0, 1).cuda()
        self.full_proj_transform = (
            self.world_view_transform.unsqueeze(0).bmm(self.projection_matrix.unsqueeze(0))).squeeze(0)
        self.camera_center = self.world_view_transform.inverse()[3, :3]


class MiniCam2:
    def __init__(self, orbit_cam):
        c2w, width, height, fovy, fovx, znear, zfar = \
            orbit_cam.pose, orbit_cam.W, orbit_cam.H, orbit_cam.fovy, orbit_cam.fovx, orbit_cam.near, orbit_cam.far
        # c2w (pose) should be in NeRF convention.
        self.image_width = width
        self.image_height = height
        self.FoVy = fovy
        self.FoVx = fovx
        self.znear = znear
        self.zfar = zfar

        w2c = np.linalg.inv(c2w)

        # rectify...
        w2c[1:3, :3] *= -1
        w2c[:3, 3] *= -1

        self.world_view_transform = torch.tensor(w2c).transpose(0, 1).cuda()

        self.projection_matrix = (
            getProjectionMatrix(
                znear=self.znear, zfar=self.zfar, fovX=self.FoVx, fovY=self.FoVy
            )
            .transpose(0, 1)

            .cuda()
        )

        self.full_proj_transform = self.world_view_transform @ self.projection_matrix

        self.camera_center = -torch.tensor(c2w[:3, 3]).cuda()

    def update(self, orbit_cam):
        self.__init__(orbit_cam)

