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
# Modified by Jeremy, 2024

from typing import NamedTuple
import torch
from . import _C


class GaussianRasterizationSettings(NamedTuple):
    image_height: int
    image_width: int
    tanfovx: float
    tanfovy: float
    bg: torch.Tensor
    scale_modifier: float
    viewmatrix: torch.Tensor
    projmatrix: torch.Tensor
    sh_degree: int
    campos: torch.Tensor
    prefiltered: bool
    debug: bool


class GaussianRasterizer:
    def __init__(self, raster_settings):
        super().__init__()
        self.raster_settings = raster_settings

    def __call__(self, means3D, means2D, opacities, shs, scales, rotations,
                 opaque_depths, camera_near, camera_far):

        colors_precomp = torch.Tensor([])
        cov3Ds_precomp = torch.Tensor([])

        args = (
            self.raster_settings.bg,
            means3D,
            colors_precomp,
            opacities,
            scales,
            rotations,
            self.raster_settings.scale_modifier,
            cov3Ds_precomp,
            self.raster_settings.viewmatrix,
            self.raster_settings.projmatrix,
            self.raster_settings.tanfovx,
            self.raster_settings.tanfovy,
            self.raster_settings.image_height,
            self.raster_settings.image_width,
            shs,
            self.raster_settings.sh_degree,
            self.raster_settings.campos,
            self.raster_settings.prefiltered,
            opaque_depths,
            camera_near,
            camera_far,
            self.raster_settings.debug
        )

        # Invoke C++/CUDA rasterizer
        color = _C.rasterize_gaussians(*args)
        return color
