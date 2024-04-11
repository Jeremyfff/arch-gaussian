# 各类换算、计算
import numpy as np


def depth_attachment_value_to_linear_depth(value, far, near):
    """深度缓冲区中的0-1的深度值转线性真实距离"""
    if value == 1.0:
        return None
    return (2 * far * near) / ((far + near) - value * (far - near))


def xzy_space_to_xyz_space(pos: np.ndarray):
    """y轴向上，转z轴向上"""
    return np.array([pos[0], pos[2], -pos[1]])


def get_ray_from_camera(camera_position, camera_forward, fov_x, fov_y, screen_point):
    """
    camera position: xzy space
    camera forward: xzy space
    fov_x: radius
    fov_y: radius
    screen_point (0-1)
    """

    # 将屏幕空间坐标转换为裁剪空间坐标
    clip_point = np.array([screen_point[0] * 2 - 1, 1 - screen_point[1] * 2, screen_point[2]])

    # 计算视图空间坐标
    view_point = np.array([clip_point[0] * np.tan(0.5 * fov_x), clip_point[1] * np.tan(0.5 * fov_y), -1])

    # 计算射线的方向向量
    ray_direction = view_point - camera_position
    ray_direction /= np.linalg.norm(ray_direction)  # 归一化
