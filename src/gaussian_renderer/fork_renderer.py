import math

import torch
from diff_gaussian_rasterization_fork import GaussianRasterizationSettings, GaussianRasterizer

from scene.gaussian_model import GaussianModel

rasterizer = GaussianRasterizer(raster_settings=None)


def render(viewpoint_camera,
           pc: GaussianModel,
           bg_color: torch.Tensor,
           opaque_depth: torch.Tensor = None):
    """
    Render the scene.
    """

    raster_settings = GaussianRasterizationSettings(
        image_height=int(viewpoint_camera.image_height),
        image_width=int(viewpoint_camera.image_width),
        tanfovx=math.tan(viewpoint_camera.FoVx * 0.5),
        tanfovy=math.tan(viewpoint_camera.FoVy * 0.5),
        bg=bg_color,
        scale_modifier=1.0,
        viewmatrix=viewpoint_camera.world_view_transform,
        projmatrix=viewpoint_camera.full_proj_transform,
        sh_degree=pc.active_sh_degree,
        campos=viewpoint_camera.camera_center,
        prefiltered=False,
        debug=False
    )

    global rasterizer
    rasterizer.raster_settings = raster_settings

    means3D = pc.get_xyz
    opacity = pc.get_opacity
    scales = pc.get_scaling
    rotations = pc.get_rotation
    shs = pc.get_features
    rendered_image = rasterizer(
        means3D=means3D,
        means2D=None,
        shs=shs,
        opacities=opacity,
        scales=scales,
        rotations=rotations,
        opaque_depths=opaque_depth,
        camera_near=viewpoint_camera.projection.near,
        camera_far=viewpoint_camera.projection.far,
    )

    return rendered_image
