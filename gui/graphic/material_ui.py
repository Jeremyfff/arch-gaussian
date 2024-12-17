# -*- coding: utf-8 -*-
# @Author  : Yiheng Feng
# @Time    : 12/11/2024 11:10 AM
# @Function:
import logging

import imgui

from gui.components import c
from gui.global_info import *

__runtime__ = True

import moderngl

from gui.modules import TextureModule

if not __runtime__:
    from gui.graphic.material import IMaterial


class IComponent:
    def show(self):
        raise NotImplementedError


class FloatComponent(IComponent):
    def __init__(self, host: "IMaterial", key: str):
        self.host = host
        self.key = key

    def show(self):
        changed, value = imgui.drag_float(self.key, self.host[self.key])
        if changed:
            self.host[self.key] = value


class IntComponent(IComponent):
    def __init__(self, host: "IMaterial", key: str):
        self.host = host
        self.key = key

    def show(self):
        changed, value = imgui.drag_int(self.key, self.host[self.key])
        if changed:
            self.host[self.key] = value


class Float2Component(IComponent):
    def __init__(self, host: "IMaterial", key: str):
        self.host = host
        self.key = key

    def show(self):
        changed, values = imgui.drag_float2(self.key, *self.host[self.key])
        if changed:
            self.host[self.key] = values


class Float3Component(IComponent):
    def __init__(self, host: "IMaterial", key: str):
        self.host = host
        self.key = key

    def show(self):
        changed, values = imgui.drag_float3(self.key, *self.host[self.key])
        if changed:
            self.host[self.key] = values


class Float4Component(IComponent):
    def __init__(self, host: "IMaterial", key: str):
        self.host = host
        self.key = key

    def show(self):
        changed, values = imgui.drag_float4(self.key, *self.host[self.key])
        if changed:
            self.host[self.key] = values


class Color3Component(IComponent):
    def __init__(self, host: "IMaterial", key: str):
        self.host = host
        self.key = key

    def show(self):
        changed, values = imgui.color_edit3(self.key, *self.host[self.key])
        if changed:
            self.host[self.key] = values


class Color4Component(IComponent):
    def __init__(self, host: "IMaterial", key: str):
        self.host = host
        self.key = key

    def show(self):
        changed, values = imgui.color_edit4(self.key, *self.host[self.key])
        if changed:
            self.host[self.key] = values


class PreservedTextureComponent(IComponent):
    def __init__(self, host: "IMaterial", key: str):
        self.host = host
        self.key = key
        self.location = PRESERVED_TEXTURE_LOCATIONS[key]

    def show(self):
        imgui.text(f"Preserved Texture: {self.key} at {self.location}")


class TextureComponent(IComponent):
    def __init__(self, host: "IMaterial", key: str):
        self.host = host
        self.key = key
        self.location = host.values[key]

    def show(self):
        tex_or_sampler = self.host.textures[self.key]
        if tex_or_sampler is None:
            tex = TextureModule.get_texture("Default_ChessBoard")
            c.image_button_using_glo(tex.glo)
            imgui.same_line()
            imgui.text(f"Texture: {self.key} at {self.location} (no data)")
        elif isinstance(tex_or_sampler, moderngl.Texture):
            tex: moderngl.Texture = tex_or_sampler
            c.image_button_using_glo(tex.glo)
            imgui.same_line()
            imgui.text(f"Texture: {self.key} at {self.location}")
        else:
            sampler: moderngl.Sampler = tex_or_sampler
            tex = sampler.texture
            imgui.text(f"Sampler not supported yet")


class MaterialUI:
    def __init__(self, host: "IMaterial"):
        self.host = host
        self.components: list[IComponent] = []
        self.components_for_textures: list[IComponent] = []
        self.components_for_preserved_textures: list[IComponent] = []
        for key in host.values.keys():
            value = self.host.prog[key].value  # use prog value instead of host.values
            if key in PRESERVED_TEXTURE_LOCATIONS:
                self.components_for_preserved_textures.append(PreservedTextureComponent(host, key))
                continue
            if key in host.textures:
                self.components_for_textures.append(TextureComponent(host, key))
                continue
            if isinstance(value, float):
                self.components.append(FloatComponent(host, key))
            elif isinstance(value, tuple):
                if len(value) == 2:
                    self.components.append(Float2Component(host, key))
                elif len(value) == 3:
                    if "color" in key.lower():
                        self.components.append(Color3Component(host, key))
                    else:
                        self.components.append(Float3Component(host, key))
                elif len(value) == 4:
                    if "color" in key.lower():
                        self.components.append(Color4Component(host, key))
                    else:
                        self.components.append(Float4Component(host, key))
            elif isinstance(value, int):
                self.components.append(IntComponent(host, key))
            else:
                logging.warning(f"unsupported value type: {type(value)}, value = {value}, key = {key}, type module = {type(value).__module__}")

    def operation_panel(self):
        imgui.push_id(self.host.uid)
        imgui.text(self.host.name)
        if imgui.tree_node("Values", imgui.TREE_NODE_DEFAULT_OPEN):
            for component in self.components:
                component.show()
            for component in self.components_for_textures:
                component.show()
            for component in self.components_for_preserved_textures:
                component.show()

            imgui.tree_pop()
        if imgui.tree_node("Defines"):
            for key, value in self.host.defines.items():
                imgui.text(f"{key} : {value}")
            imgui.tree_pop()
        if imgui.tree_node("Misc"):
            changed, new_cast_shadows = imgui.checkbox("Cast Shadows", self.host.cast_shadows)
            if changed:
                self.host.cast_shadows = new_cast_shadows
            changed, new_receive_shadows = imgui.checkbox("Receive Shadows", self.host.receive_shadows)
            if changed:
                self.host.receive_shadows = new_receive_shadows
            imgui.tree_pop()
        imgui.pop_id()
