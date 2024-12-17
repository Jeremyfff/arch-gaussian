__runtime__ = True

import abc
import math

import imgui
from pyrr import Vector3, Vector4
from gui.utils import color_utils
from gui.user_data import user_settings

if not __runtime__:
    from gui.graphic import geometry_component as geoc


class IComponentUI:
    @abc.abstractmethod
    def operation_panel(self):
        raise NotImplementedError


class TransformComponentUI(IComponentUI):
    def __init__(self, host: "geoc.TransformComponent"):
        self.host = host
        self._imgui_translation = tuple(host.translation.tolist())
        self._imgui_rotation = tuple((host.rotation * 180.0 / math.pi).tolist())  # in degree
        self._imgui_scale = tuple(host.scale.tolist())

    def operation_panel(self):
        # region TRANSITION
        translation_changed, self._imgui_translation = imgui.drag_float3(
            'Translation',
            *self._imgui_translation,
            user_settings.move_scroll_speed
        )
        if translation_changed:
            self.host.translation = Vector3(self._imgui_translation)
        # endregion

        # region ROTATION

        rotation_changed, self._imgui_rotation = imgui.drag_float3(
            'Rotation',
            *self._imgui_rotation,
            user_settings.rotate_scroll_speed
        )
        if rotation_changed:
            self.host.rotation = Vector3(
                (
                    math.radians(self._imgui_rotation[0]),
                    math.radians(self._imgui_rotation[1]),
                    math.radians(self._imgui_rotation[2])
                )
            )
        # endregion

        # region SCALE
        scale_changed, self._imgui_scale = imgui.drag_float3(
            'Scale',
            *self._imgui_scale,
            user_settings.scale_scroll_speed,
            0.0
        )
        if scale_changed:
            self.host.scale = Vector3(self._imgui_scale)

        # endregion


class DirectionalLightComponentUI(IComponentUI):
    def __init__(self, host: "geoc.DirectionalLightComponent"):
        self.host = host
        self._imgui_color = self.host.geometry.color.tolist()
        self._imgui_kelvin_temp = 6500
        self._imgui_range = self.host.geometry.range
        self._imgui_custom_direction = self.host.geometry.direction.tolist()
    def operation_panel(self):
        changed, self.host.show_indicator = imgui.checkbox("Show Indicator", self.host.show_indicator)

        # ===================================================
        changed, self._imgui_color = imgui.color_edit3("Sun Color", *self._imgui_color)
        if changed:
            self.host.geometry.color = Vector3(self._imgui_color, dtype="f4")
        changed, self._imgui_kelvin_temp = imgui.slider_int("Temperature", self._imgui_kelvin_temp, 1000, 10000)
        if changed:
            self._imgui_color = color_utils.k_to_rgb(self._imgui_kelvin_temp)
            self.host.geometry.color = Vector3(self._imgui_color, dtype="f4")

        changed, self._imgui_range = imgui.drag_float("Range", self._imgui_range, 0.1, 1.0, 100.0)
        if changed:
            self.host.geometry.range = self._imgui_range

        changed, self._imgui_custom_direction = imgui.drag_float3("custom dir", *self._imgui_custom_direction, 0.01, -1.0, 1.0)
        if changed:
            self.host.geometry.direction = Vector3(self._imgui_custom_direction, dtype="f4")