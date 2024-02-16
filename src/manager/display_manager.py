import copy

import numpy as np
from PIL import Image, ImageDraw


def to_homogeneous_points(points: np.ndarray):
    assert isinstance(points, np.ndarray), "points must be numpy.ndarray"
    if points.ndim == 1:
        points = np.reshape(points, (1, points.shape[0]))
        print(points.shape)
    assert points.ndim == 2, "points dim must be 2"
    if points.shape[0] == 4:
        return points
    return np.hstack((points, np.ones((points.shape[0], 1))))


def world2screen(points, cam):
    homogeneous_points = to_homogeneous_points(points)

    view_matrix = cam.world_view_transform.transpose(0, 1).cpu().numpy()
    projection_matrix = cam.projection_matrix.transpose(0, 1).cpu().numpy()

    transformed_points = np.matmul(view_matrix, homogeneous_points.T).T
    transformed_points = np.matmul(projection_matrix, transformed_points.T).T

    screen_points = transformed_points[:, :2] / transformed_points[:, 2:]  # 添加透视除法

    screen_points[:, 0] = screen_points[:, 0] * cam.image_width / 2 + cam.image_width / 2
    screen_points[:, 1] = screen_points[:, 1] * cam.image_height / 2 + cam.image_height / 2
    return screen_points



class Geometry:
    def __init__(self, points, edges):
        self.points = points
        self.edges = edges
        self.point_radius = 10
        self.point_color = 'red'
        self.line_width = 5
        self.line_color = 'green'

    def draw(self, cam, drawer):
        screen_points = world2screen(self.points, cam)
        for point in screen_points:
            drawer.ellipse([point[0] - self.point_radius,
                            point[1] - self.point_radius,
                            point[0] + self.point_radius,
                            point[1] + self.point_radius],
                           fill=self.point_color)
        for edge in self.edges:
            start = screen_points[edge[0]]
            end = screen_points[edge[1]]
            drawer.line(np.array([start, end]), fill=self.line_color, width=self.line_width)

class Box(Geometry):
    def __init__(self, a, b):
        cube_points = np.array([
            [a[0], a[1], a[2]],  # 左下后
            [a[0], b[1], a[2]],  # 左上后
            [b[0], a[1], a[2]],  # 右下后
            [b[0], b[1], a[2]],  # 右上后

            [a[0], a[1], b[2]],  # 左下前
            [a[0], b[1], b[2]],  # 左上前
            [b[0], a[1], b[2]],  # 右下前
            [b[0], b[1], b[2]],  # 右上前
        ])
        edges = [
            (0, 1), (1, 3), (3, 2), (2, 0),  # 左边
            (4, 5), (5, 7), (7, 6), (6, 4),  # 右边
            (0, 4), (1, 5), (2, 6), (3, 7)  # 连接前后面
        ]
        super().__init__(cube_points, edges)


class Drawer:
    def __init__(self, ):
        self.geometries: list[Geometry] = []

    def add_geometry(self, geometry: Geometry):
        self.geometries.append(geometry)

    def draw(self, cam, base_image, overwrite=False):
        if overwrite:
            new_image = base_image
        else:
            new_image = copy.deepcopy(base_image)
        drawer = ImageDraw.Draw(new_image)
        for geo in self.geometries:
            geo.draw(cam, drawer)
        return new_image

