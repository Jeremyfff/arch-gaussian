import copy
import json
import os
from contextlib import contextmanager
from functools import reduce
from typing import Optional

import numpy as np
import torch
from pyrr import Matrix44
from torch import Tensor

from scene import GaussianModel
from utils.arg_utils import parse_args
from utils.image_utils import get_pil_image


def create_gaussian_from_ply(sh_degree, path):
    _gaussians = GaussianModel(sh_degree)
    _gaussians.load_ply(path)
    return _gaussians


def create_gaussian_from_scene_info(sh_degree, scene_info):
    _gaussians = GaussianModel(sh_degree)
    cameras_extent = scene_info.nerf_normalization["radius"]
    _gaussians.create_from_pcd(scene_info.point_cloud, cameras_extent)
    return _gaussians


class GaussianManager:
    def __init__(self, args,
                 scene_info,
                 custom_ply_path=None):
        """

        :param args:
        :param scene_info:
        :param custom_ply_path:
        """
        self.args = args
        lp, op, pp = parse_args(args)
        dataset, opt, pipe, testing_iterations, saving_iterations, checkpoint_iterations, checkpoint, debug_from = lp.extract(
            args), op.extract(args), pp.extract(
            args), args.test_iterations, args.save_iterations, args.checkpoint_iterations, args.start_checkpoint, args.debug_from
        self.pipe = pipe
        self.source_ply_path = ''  # 追踪gaussian 源自哪个ply
        if custom_ply_path is not None:
            # 如果有custom ply path， 则使用自定义的路径创建gaussian
            print("[Gaussian Manager] Creating gaussians from custom ply")
            self.source_ply_path = custom_ply_path
            self.gaussians = create_gaussian_from_ply(args.sh_degree, custom_ply_path)

        elif args.loaded_iter:
            print("[Gaussian Manager] Creating gaussians from ply")
            self.source_ply_path = os.path.join(args.model_path, "point_cloud", "iteration_" + str(args.loaded_iter), "point_cloud.ply")
            self.gaussians = create_gaussian_from_ply(args.sh_degree, self.source_ply_path)
        else:
            print("[Gaussian Manager] Creating gaussians from scene info")
            self.gaussians = create_gaussian_from_scene_info(args.sh_degree, scene_info)

        self.bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
        self.bg_backup = None
        self.gaussians_backup = None

        # 加载渲染后端
        from gaussian_renderer.default_renderer import render
        self._render_function = render  # default renderer
        from gaussian_renderer.fork_renderer import render
        self._render_function_fork = render  # for fast rendering

    # region 缓存相关
    @contextmanager
    def virtual(self):
        # 进入代码块前执行的操作
        print("[Gaussian Manager] Entering the code block")
        self.cache()
        try:
            # yield之前的代码相当于__enter__方法
            yield
        finally:
            self.restore()

    def cache(self):
        self.gaussians_backup = self.gaussians
        self.gaussians = copy.deepcopy(self.gaussians)
        self.bg_backup = self.bg
        self.bg = copy.deepcopy(self.bg)

    def restore(self):
        if self.gaussians_backup is None:
            return
        self.gaussians = self.gaussians_backup
        del self.gaussians_backup
        self.gaussians_backup = None
        self.bg = self.bg_backup
        del self.bg_backup
        self.bg_backup = None

    def has_cache(self):
        return self.gaussians_backup is not None

    def apply(self):
        """
        应用改变
        """
        self.gaussians_backup = self.gaussians
        self.bg_backup = self.bg

    def clear_cache(self):
        self.gaussians_backup = None
        self.bg_backup = None

    # endregion

    # region 渲染
    def render(self,
               camera,
               convert_to_pil=False,
               convert_to_rgba_arr=False,
               convert_to_rgb_arr=False,
               ):
        """default render for gaussian splatting training"""
        with torch.no_grad():
            render_pkg = self._render_function(camera, self.gaussians, self.pipe, self.bg)
            image = render_pkg["render"]

            if convert_to_pil:
                image = get_pil_image(image)
            elif convert_to_rgba_arr:
                image_rgb = image.clamp(0.0, 1.0).cpu().numpy().transpose((1, 2, 0))
                alpha_channel = np.ones((image_rgb.shape[0], image_rgb.shape[1], 1))
                image_rgba = np.concatenate((image_rgb, alpha_channel), axis=2)
                image_rgba = (image_rgba * 255).astype(np.uint8)
                image = image_rgba
            elif convert_to_rgb_arr:
                image_rgb = image.clamp(0.0, 1.0).cpu().numpy().transpose((1, 2, 0))
                image_rgb = (image_rgb * 255).astype(np.uint8)
                image = image_rgb
        return image

    def render_fork(self, camera, opaque_depth) -> torch.Tensor:
        """custom render function for fast rendering"""
        with torch.no_grad():
            image = self._render_function_fork(
                viewpoint_camera=camera,
                pc=self.gaussians,
                bg_color=self.bg,
                opaque_depth=opaque_depth
            )
        return image

    def visualize_in_o3d(self):
        """已弃用， 在open3d中预览"""
        import open3d as o3d
        geometries = []
        point_cloud = o3d.geometry.PointCloud()
        points = self.gaussians._xyz.detach().cpu().numpy().astype(np.float32)
        point_cloud.points = o3d.utility.Vector3dVector(points)

        SH_C0 = 0.28209479177387814
        rgb = self.gaussians._features_dc.detach().cpu().numpy()
        rgb = rgb.reshape((rgb.shape[0], 3))
        rgb = (0.5 + SH_C0 * rgb)
        rgb = np.clip(rgb, 0.0, 1.0).astype(np.float32)
        print(rgb.shape)
        point_cloud.colors = o3d.utility.Vector3dVector(rgb)
        geometries.append(point_cloud)

        # 创建numpy数组表示三条线段的起点和终点
        start_points = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
        end_points = np.array([[2, 0, 0], [0, 2, 0], [0, 0, 3]])
        # 创建LineSet对象
        axis_lines = o3d.geometry.LineSet()
        axis_lines.points = o3d.utility.Vector3dVector(np.concatenate([start_points, end_points], axis=0))
        axis_lines.lines = o3d.utility.Vector2iVector(np.array([[0, 3], [1, 4], [2, 5]]))
        axis_lines.colors = o3d.utility.Vector3dVector(
            np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]).astype(np.float32))
        geometries.append(axis_lines)

        o3d.visualization.draw_geometries(geometries)

    # endregion

    # region 创建与修改mask
    def zero_like_mask(self):
        return torch.zeros((self.gaussians.get_xyz.shape[0]), dtype=torch.bool, device='cuda')

    def ones_like_mask(self):
        return torch.ones((self.gaussians.get_xyz.shape[0]), dtype=torch.bool, device='cuda')

    def position_mask(self, min, max):
        """
        @Jeremy
        min max 推荐为torch.tensor格式
        程序会自动将其转换为tensor并传至GPU
        """
        if isinstance(min, np.ndarray) or isinstance(max, np.ndarray):
            min: Tensor = torch.tensor(min)
            max: Tensor = torch.tensor(max)

        min: Tensor = min.cuda()
        max: Tensor = max.cuda()

        with torch.no_grad():
            xyz: Tensor = self.gaussians.get_xyz
            # 使用比较运算符筛选点
            mask = (xyz[:, 0] >= min[0]) & (xyz[:, 0] <= max[0]) & \
                   (xyz[:, 1] >= min[1]) & (xyz[:, 1] <= max[1]) & \
                   (xyz[:, 2] >= min[2]) & (xyz[:, 2] <= max[2])
        return mask

    def bboxes_from_json(self, json_path, z_min, z_max):
        """
        @Jeremy
        数据结构如下：第一层级为regions， 第二层级为每个region的bboxes
        [region][bboxes]
        """
        bboxes = []
        with open(json_path, 'r') as file:
            gaussian_asset_data = json.load(file)
        regions = gaussian_asset_data['regions']
        for region in regions:
            bboxes_per_region = []
            bound_datas = region['boundDataArr']
            for bound in bound_datas:
                x_min, y_min, x_max, y_max = bound['xMin'], bound['yMin'], bound['xMax'], bound['yMax']
                bbox = (np.array([x_min, y_min, z_min]), np.array([x_max, y_max, z_max]))
                bboxes_per_region.append(bbox)
            bboxes.append(bboxes_per_region)
        return bboxes

    def masks_from_json(self, json_path):
        """
        @Jeremy
        为每一个region创建一个mask
        注意，可能会占用大量显存
        """
        masks = []
        bboxes = self.bboxes_from_json(json_path, -100, 100)
        for region in bboxes:
            mask = self.zero_like_mask()
            for bbox in region:
                mask |= self.position_mask(*bbox)
            masks.append(mask)
        return masks

    def mask_from_json(self, json_path):
        """
        @Jeremy
        所有region共享一个mask
        """
        mask = self.zero_like_mask()
        bboxes = self.bboxes_from_json(json_path, -100, 100)
        for region in bboxes:
            for bbox in region:
                mask |= self.position_mask(*bbox)
        return mask

    @staticmethod
    def combine_masks(masks: list):
        combined_mask = reduce(torch.logical_or, masks)
        return combined_mask

    @staticmethod
    def combine_mask(mask1, mask2):
        return mask1 | mask2

    def delete_by_mask(self, mask):
        self.gaussians._xyz = self.gaussians._xyz[mask]
        self.gaussians._features_dc = self.gaussians._features_dc[mask]
        self.gaussians._features_rest = self.gaussians._features_rest[mask]
        self.gaussians._scaling = self.gaussians._scaling[mask]
        self.gaussians._rotation = self.gaussians._rotation[mask]
        self.gaussians._opacity = self.gaussians._opacity[mask]

        if self.gaussians.max_radii2D.shape[0] == mask.shape[0]:
            self.gaussians.max_radii2D = self.gaussians.max_radii2D[mask]
        if self.gaussians.xyz_gradient_accum.shape[0] == mask.shape[0]:
            self.gaussians.xyz_gradient_accum = self.gaussians.xyz_gradient_accum[mask]
        if self.gaussians.denom.shape[0] == mask.shape[0]:
            self.gaussians.denom = self.gaussians.denom[mask]

    # endregion

    # region 高斯操作-颜色
    def set_color(self, color: float, mask=None):
        with torch.no_grad():
            if mask is None:
                self.gaussians._features_dc[:] = GaussianManager.rgb2feature_dc(color)
            else:
                self.gaussians._features_dc[mask] = GaussianManager.rgb2feature_dc(color)

    def set_rgb(self, rgb_color, mask=None):
        with torch.no_grad():
            color = GaussianManager.rgb2feature_dc(rgb_color)
            color = torch.tensor(color, device="cuda")
            if mask is None:
                self.gaussians._features_dc[:, 0, :] = color
            else:
                self.gaussians._features_dc[mask, 0, :] = color

    def set_alpha(self, alpha: float, mask=None):
        with torch.no_grad():
            if mask is None:
                self.gaussians._opacity[:] = GaussianManager.rgb2feature_dc(alpha)
            else:
                self.gaussians._opacity[mask] = GaussianManager.rgb2feature_dc(alpha)

    def clear_features_rest(self, mask=None):
        with torch.no_grad():
            if mask is None:
                self.gaussians._features_rest *= 0
            else:
                self.gaussians._features_rest[mask] = 0

    def paint_by_mask(self, mask):
        with torch.no_grad():
            self.bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
            self.clear_features_rest()
            self.set_color(0, ~mask)
            self.set_color(1, mask)

    def paint_by_distance(self, camera):
        with torch.no_grad():
            raise NotImplementedError

    def add_position_noise(self, std, mask=None):
        with torch.no_grad():
            if mask is None:
                size = self.gaussians._xyz.shape
                noise = np.random.normal(0.0, std, size=size)
                noise = torch.tensor(noise).cuda()
                self.gaussians._xyz += noise

            else:
                size = self.gaussians._xyz[mask].shape
                noise = np.random.normal(0.0, std, size=size)
                noise = torch.tensor(noise).cuda()
                self.gaussians._xyz[mask] += noise

    def add_color_noise(self, std, mask=None):
        with torch.no_grad():
            if mask is None:
                size = self.gaussians._features_dc.shape
                noise = np.random.normal(0.0, abs(GaussianManager.rgb2feature_dc(std)), size=size)
                noise = torch.tensor(noise).cuda()
                self.gaussians._features_dc += noise

            else:
                size = self.gaussians._features_dc[mask].shape
                noise = np.random.normal(0.0, abs(GaussianManager.rgb2feature_dc(std)), size=size)
                noise = torch.tensor(noise).cuda()
                self.gaussians._features_dc[mask] += noise

    def noise_position(self, mask, bbox):
        x_range = (bbox[0][0], bbox[1][0])
        y_range = (bbox[0][1], bbox[1][1])
        z_range = (bbox[0][2], bbox[1][2])
        # 生成随机点
        num_points = self.gaussians._xyz[mask].shape[0]  # 点的数量
        x = np.random.uniform(x_range[0], x_range[1], size=num_points)
        y = np.random.uniform(y_range[0], y_range[1], size=num_points)
        z = np.random.uniform(z_range[0], z_range[1], size=num_points)

        points = np.column_stack((x, y, z)).astype(np.float32)
        points = torch.tensor(points).cuda()
        print(points.shape)
        with torch.no_grad():
            print(self.gaussians._xyz[mask].shape)
            self.gaussians._xyz[mask] = points

    # endregion

    # region 清空梯度
    @staticmethod
    def _clear_grad(param, mask):
        if param.grad is None:
            return
        param.grad[mask] = 0

    def clear_grads(self, mask):
        self._clear_grad(self.gaussians._features_dc, mask)
        self._clear_grad(self.gaussians._features_rest, mask)
        self._clear_grad(self.gaussians._xyz, mask)
        self._clear_grad(self.gaussians._scaling, mask)
        self._clear_grad(self.gaussians._rotation, mask)
        self._clear_grad(self.gaussians._opacity, mask)

    # endregion

    # region 移动旋转
    def move(self, offset):
        offset = torch.tensor(offset, dtype=torch.float32).cuda()
        with torch.no_grad():
            self.gaussians._xyz = self.gaussians._xyz + offset

    def rotate(self, matrix: Matrix44):
        matrix44 = torch.tensor(matrix, dtype=torch.float32).cuda()
        matrix33 = torch.tensor(matrix.matrix33, dtype=torch.float32).cuda()
        with torch.no_grad():
            # self.gaussians._xyz = torch.matmul(self.gaussians._xyz, matrix33)
            self.gaussians._rotation = torch.dot(self.gaussians._rotation, matrix44.t())
            # self.gaussians._scaling = torch.matmul(self.gaussians._scaling, matrix33)

    # endregion
    # region static methods
    @staticmethod
    def rgb2feature_dc(data):
        return (data - 0.5) / 0.28209479177387814

    @staticmethod
    def feature_dc2rgb(data):
        return data * 0.28209479177387814 + 0.5

    @staticmethod
    def feature_opacity2alpha(data):
        return 1 / (1 + torch.exp(-data))

    @staticmethod
    def alpha2feature_opacity(a):
        assert a != 0 and a != 1, "a cannot be zero or one"
        return torch.log(a / (1 - a))

    @staticmethod
    def merge_gaussian_managers(gms: list["GaussianManager"]) -> Optional["GaussianManager"]:
        if len(gms) == 0:
            return None
        if len(gms) == 1:
            return gms[0]

        with torch.no_grad():
            final_gm = copy.deepcopy(gms[0])
            final_gm.clear_cache()
            final_xyz_list = []
            final_features_dc_list = []
            final_features_rest_list = []
            final_scaling_list = []
            final_rotation_list = []
            final_opacity_list = []
            final_max_radii2D_list = []
            for i, gm in enumerate(gms):
                gaussians = gm.gaussians
                final_xyz_list.append(gaussians._xyz.detach())
                final_features_dc_list.append(gaussians._features_dc.detach())
                final_features_rest_list.append(gaussians._features_rest.detach())
                final_scaling_list.append(gaussians._scaling.detach())
                final_rotation_list.append(gaussians._rotation.detach())
                final_opacity_list.append(gaussians._opacity.detach())
                final_max_radii2D_list.append(gaussians.max_radii2D.detach())

            final_gm.gaussians._xyz = torch.cat(final_xyz_list, dim=0)
            final_gm.gaussians._features_dc = torch.cat(final_features_dc_list, dim=0)
            final_gm.gaussians._features_rest = torch.cat(final_features_rest_list, dim=0)
            final_gm.gaussians._scaling = torch.cat(final_scaling_list, dim=0)
            final_gm.gaussians._rotation = torch.cat(final_rotation_list, dim=0)
            final_gm.gaussians._opacity = torch.cat(final_opacity_list, dim=0)
            final_gm.gaussians.max_radii2D = torch.cat(final_max_radii2D_list, dim=0)
            return final_gm
    # endregion
