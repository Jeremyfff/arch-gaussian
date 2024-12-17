# -*- coding: utf-8 -*-
# @Author  : Yiheng Feng
# @Time    : 12/12/2024 5:10 PM
# @Function:

__runtime__ = True

import logging
from functools import cached_property
from typing import Union

from pyrr import Vector3, Matrix44

from gui.graphic import geometry_component_ui as ui
from gui.utils import transform_utils

if not __runtime__:
    from gui.graphic import geometry


class IComponent:
    def __init__(self, geo):
        self.geometry = geo

    def update(self):
        pass

    def on_enable(self):
        pass

    def on_disable(self):
        pass

    def operation_panel(self):
        pass


class TransformComponent(IComponent):
    def __init__(self, geo: "geometry.BaseGeometry"):
        super().__init__(geo)

        self._parent_rotation = Vector3((0., 0., 0.), dtype="f4")  # parent rotation in radius
        self._parent_translation = Vector3((0., 0., 0.), dtype="f4")  # parent transition
        self._rotation = Vector3((0., 0., 0.), dtype="f4")  # local rotation in radius
        self._translation = Vector3((0., 0., 0.), dtype="f4")  # local translation
        self._scale = Vector3((1., 1., 1.), dtype="f4")  # local scale

        self.world_matrix = transform_utils.world_matrix
        self.world_matrix_33 = transform_utils.world_matrix_33
        self.world_matrix_inv = transform_utils.world_matrix_inv
        self.world_matrix_inv_33 = transform_utils.world_matrix_inv_33
        self.gl_up = transform_utils.gl_up
        self.world_up = transform_utils.world_up

        self._ui = ui.TransformComponentUI(self)
        self._cached_property_names = ["world_translation", "world_rotation", "model_view", "model_view_with_no_world_matrix"]

    def on_enable(self):
        logging.info(f"{self.geometry.name} - Transform - on_enable")

    def on_disable(self):
        logging.info(f"{self.geometry.name} - Transform - on_disable")

    @property
    def translation(self) -> Vector3:
        return self._translation

    @translation.setter
    def translation(self, value: Union[Vector3, tuple[float]]):
        if not isinstance(value, Vector3):
            value = Vector3(value, dtype="f4")
        self._translation = value
        self._on_transform_changed()

    @property
    def rotation(self) -> Vector3:
        return self._rotation

    @rotation.setter
    def rotation(self, value: Union[Vector3, tuple[float]]):
        if not isinstance(value, Vector3):
            value = Vector3(value, dtype="f4")
        self._rotation = value
        self._on_transform_changed()

    @property
    def scale(self) -> Vector3:
        return self._scale

    @scale.setter
    def scale(self, value: Union[Vector3, tuple[float]]):
        if not isinstance(value, Vector3):
            value = Vector3(value, dtype="f4")
        self._scale = value
        self._on_transform_changed()

    def _on_transform_changed(self):
        # delete cached properties
        for prop in self._cached_property_names:
            if prop in self.__dict__:
                self.__dict__.pop(prop)

    @cached_property
    def world_translation(self):
        """获取世界平移"""
        return self._parent_translation + self._translation

    @cached_property
    def world_rotation(self):
        """获取世界旋转"""
        return self._parent_rotation + self._rotation

    @cached_property
    def model_view(self):
        rotation = Matrix44.from_eulers(self.world_rotation, dtype='f4')
        translation = Matrix44.from_translation(self.world_translation, dtype='f4')
        scale = Matrix44.from_scale(self.scale, dtype='f4')
        model_view = self.world_matrix * translation * rotation * scale
        return model_view

    @cached_property
    def model_view_with_no_world_matrix(self):
        rotation = Matrix44.from_eulers(self.world_rotation, dtype='f4')
        translation = Matrix44.from_translation(self.world_translation, dtype='f4')
        scale = Matrix44.from_scale(self.scale, dtype='f4')
        model_view = translation * rotation * scale
        return model_view

    @staticmethod
    def to_gl_space(vec: Vector3) -> Vector3:
        return transform_utils.to_gl_space(vec)

    @staticmethod
    def from_gl_space(vec: Vector3):
        return transform_utils.from_gl_space(vec)

    def operation_panel(self):
        self._ui.operation_panel()


class DirectionalLightComponent(IComponent):
    def __init__(self, geo: "geometry.DirectionalLight"):
        super().__init__(geo)
        self.geometry: "geometry.DirectionalLight" = self.geometry

        self.show_indicator = True
        self._ui = ui.DirectionalLightComponentUI(self)

    def operation_panel(self):
        self._ui.operation_panel()
