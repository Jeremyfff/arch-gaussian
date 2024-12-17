# 各类换算、计算
import datetime
import math

import numpy as np
import pytz
from pvlib.solarposition import get_solarposition
from pyrr import Vector3, Matrix44


def z_buffer_depth_to_linear_depth(z_buffer, far, near):
    """z_buffer 深度（0, 1） 转线性深度
    https://scarletsky.github.io/2021/03/06/gl-depth-transformation/
    """
    return (far * near) / (far - z_buffer * (far - near))


def ndc_depth_to_linear_depth(z_ndc, far, near):
    """NDC设备坐标系(-1, 1)的深度值转线性深度"""
    return (2 * far * near) / ((far + near) - z_ndc * (far - near))


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


# 获取本地时区
local_tz = pytz.timezone('Asia/Shanghai')


def get_sun_dir(latitude: float, longitude: float, year: int, month: int, day: int, hour: int, minute: int, second: int) -> Vector3:
    t = datetime.datetime(year, month, day, hour, minute, second)
    t_utc = local_tz.localize(t).astimezone(pytz.utc)

    # 创建太阳位置模型
    solar_position = get_solarposition(t_utc, latitude, longitude)

    # 获取太阳方位角和天顶角
    solar_zenith = solar_position['apparent_zenith'].values[0]
    solar_azimuth = solar_position['azimuth'].values[0]

    # 将角度转换为弧度
    zenith_rad = np.radians(solar_zenith)
    azimuth_rad = np.radians(solar_azimuth)

    # 计算单位向量
    x = np.sin(zenith_rad) * np.cos(azimuth_rad)
    y = np.sin(zenith_rad) * np.sin(azimuth_rad)
    z = np.cos(zenith_rad)

    # 归一化单位向量
    length = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    light_dir = -np.array([x, y, z]) / length

    return Vector3(light_dir, dtype="f4")


world_matrix = Matrix44.from_eulers((math.pi / 2, 0, 0), dtype='f4')
# world_matrix = Matrix44.identity(dtype='f4')
world_matrix_33 = world_matrix.matrix33
world_matrix_inv = world_matrix.inverse
world_matrix_inv_33 = world_matrix_inv.matrix33

gl_up = Vector3((0.0, 1.0, 0.0), dtype="f4")
world_up = Vector3((0.0, 0.0, 1.0), dtype="f4")


def to_gl_space(vec: Vector3) -> Vector3:
    return world_matrix_33 * vec


def from_gl_space(vec: Vector3):
    return world_matrix_inv_33 * vec
