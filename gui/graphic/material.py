import abc
import copy
import logging
import uuid
from functools import cached_property
from typing import Optional, Union

import moderngl
from deprecated import deprecated
from moderngl_window.opengl.program import ProgramShaders

from gui.global_info import *
from gui.graphic.material_ui import MaterialUI
from gui.modules import TextureModule
from gui.utils import graphic_utils


def support_m(prog):
    if prog.get('m_model', None) is None:
        return False
    return True


def support_mvp(prog):
    """是否支持mvp"""
    if prog.get('m_model', None) is None:
        return False
    if prog.get('m_camera', None) is None:
        return False
    if prog.get('m_proj', None) is None:
        return False
    return True


def support_cast_shadows(prog):
    return support_m(prog)


def get_default_texture_by_key(key: str):
    key = key.lower()
    if "normal" in key:
        return TextureModule.get_texture("Default_Normal")
    elif "ao" in key or "ambient" in key or "occlusion" in key:
        return TextureModule.get_texture("Default_White")
    else:
        return TextureModule.get_texture("Default_Black")


class Shader:
    def __init__(self, program_path):
        self.program_shader: ProgramShaders = graphic_utils.load_shader(program_path)

        self.default_defines = {}
        self.all_possible_sampler2Ds = set()
        for nr, line in enumerate(self.program_shader.vertex_source.lines):
            line = line.strip()
            # scan default defines
            if line.startswith("#define"):
                parts = line.split()
                if len(parts) <= 1:
                    continue
                if len(parts) > 2:
                    name = parts[1]
                    value = " ".join(parts[2:])
                    self.default_defines[name] = value
            if line.startswith("uniform sampler2D"):
                parts = line.split()
                sampler2DName = parts[2]
                sampler2DName = sampler2DName[0:-1]  # 去除分号
                self.all_possible_sampler2Ds.add(sampler2DName)
            # scan all possible sampler2Ds

        if 'VERTEX_SHADER' in self.default_defines:
            self.default_defines.pop('VERTEX_SHADER')

    def _create_material(self, name, values: dict = None, defines: dict = None, const_keys: set = None, textures: dict[str: Union[moderngl.Texture, moderngl.Sampler]] = None, is_shadow_map=False) -> "Material":

        if values is None:
            values = {}
        if defines is None:
            defines = {}
        if textures is None:
            textures = {}
        # handle defines
        for key, value in defines.items():
            assert key in self.default_defines, f"Invalid define key {key}. Cannot find this key in self.default_defines.keys(), valid keys are: {self.default_defines.keys()}"

        full_defines = copy.deepcopy(self.default_defines)
        for key, value in defines.items():
            full_defines[key] = value

        # apply defines
        assert self.program_shader.vertex_source is not None and self.program_shader.fragment_source is not None
        if is_shadow_map:
            # vertex shader保持不变
            self.program_shader.vertex_source.apply_defines(full_defines)
            # fragment shader 替换为简单版本编译
            org_lines_for_fragment_source = self.program_shader.fragment_source._lines  # 保存原有代码
            self.program_shader.fragment_source._lines = [
                "#version 420",
                "out vec4 fragColor;"
                "void main()",
                "{",
                "    fragColor = vec4(1.0);",
                "}",
            ]
            prog: moderngl.Program = self.program_shader.create()
            self.program_shader.fragment_source._lines = org_lines_for_fragment_source  # 恢复原有代码
        else:
            self.program_shader.vertex_source.apply_defines(full_defines)
            self.program_shader.fragment_source.apply_defines(full_defines)
            prog: moderngl.Program = self.program_shader.create()

        # handle uniform values
        full_values = {}
        for key, member in prog._members.items():
            if not isinstance(member, moderngl.Uniform):
                # if is moderngl.Attribute or moderngl.UniformBlock
                continue
            if isinstance(member.value, tuple) and len(member.value) > 4:
                # if is matrix
                continue
            # full values 只记录int, float vec2 vec3 vec4类型的变量
            full_values[key] = member.value

        # replace values
        for key, value in values.items():
            if key in full_values:
                full_values[key] = value
        print(f"{name}.all_possible_sampler2Ds = {self.all_possible_sampler2Ds}")
        print(f"{name}.full_values = {full_values} (is_shadow_map = {is_shadow_map})")
        # 寻找texture名称,矫正location
        _curr_max_location = -1
        full_textures = {}  # 不包含shadowMap等保留的贴图
        for key in full_values.keys():
            if key not in self.all_possible_sampler2Ds:
                continue
            print(f"find key {key} in all_possible_sampler2Ds")
            if key in PRESERVED_TEXTURE_LOCATIONS:
                location = PRESERVED_TEXTURE_LOCATIONS[key]
                full_values[key] = location  # 使用在保留位中的序号
                continue

            location = full_values[key]
            if location <= _curr_max_location:
                location = _curr_max_location + 1
                print(f"{name}.{key} location 被占用，使用下一个location: {location}")
                assert location not in PRESERVED_TEXTURE_LOCATIONS.values(), f"使用了被保留的location， 这些location不能使用: {PRESERVED_TEXTURE_LOCATIONS}"
                full_values[key] = location
                _curr_max_location = location
            else:
                print(f"{name}.{key} location没有被占用")
                _curr_max_location = location
            if key in textures:
                full_textures[key] = textures[key]
            else:
                # texture not assigned, use default texture
                full_textures[key] = None
        print(f"{name}.final_full_values = {full_values} (is_shadow_map = {is_shadow_map})")
        shadowmap_mat = None
        if support_cast_shadows(prog) and not is_shadow_map:
            shadowmap_mat = self._create_material(name, values, defines, const_keys, textures, is_shadow_map=True)

        Material._allow_init = True
        mat = Material(name, self, prog, full_values, full_defines, full_textures, const_keys, shadowmap_mat)
        Material._allow_init = False

        return mat

    def create_material(self, name, values: dict = None, defines: dict = None, const_keys: set = None, textures: dict[str: Union[moderngl.Texture, moderngl.Sampler]] = None) -> "Material":
        """



        :param name:
        :param values: dict类型， 用于替换prog._members.Uniform 的值，可以是shader程序中包含的部分参数的值，在这里出现的值将替换原始的值
        :param defines: dict类型，要替换的define， 出现的键值对必须在shader中出现
        :param const_keys:set类型，标记哪些value的key在当前材质中是恒定不变的，能够略微加速
        :param textures: dict, 用于指定默认的纹理贴图，如果没有指定，则使用默认贴图
        :return:
        """

        return self._create_material(name, values, defines, const_keys, textures)


class IMaterial:
    def __init__(self):
        self.uid = str(uuid.uuid4())

    @abc.abstractmethod
    def write_mvp(self, m_model, m_camera, m_proj):
        raise NotImplementedError

    @abc.abstractmethod
    def write_m(self, m_model):
        raise NotImplementedError

    @abc.abstractmethod
    def use(self):
        raise NotImplementedError

    @abc.abstractmethod
    def copy(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def name(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def shader(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def prog(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def values(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def default_values(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def defines(self):
        raise NotImplementedError

    @property
    def textures(self):
        raise NotImplementedError

    def set_texture(self, name, texture: Union[moderngl.Texture, moderngl.Sampler]):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def dynamic_keys(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __getitem__(self, key):
        raise NotImplementedError

    @abc.abstractmethod
    def __setitem__(self, key, value):
        raise NotImplementedError

    def operation_panel(self):
        raise NotImplementedError

    @cached_property
    @abc.abstractmethod
    def support_m(self) -> bool:
        """支持m_model"""
        raise NotImplementedError

    @cached_property
    @abc.abstractmethod
    def support_mvp(self) -> bool:
        """支持m_model, m_view, m_proj 的输入"""
        raise NotImplementedError

    @cached_property
    @abc.abstractmethod
    def support_cast_shadow(self) -> bool:
        raise NotImplementedError

    @cached_property
    @abc.abstractmethod
    def support_receive_shadow(self) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def shadowmap_mat(self) -> "IMaterial":
        raise NotImplementedError

    @property
    def cast_shadows(self) -> bool:
        raise NotImplementedError

    @cast_shadows.setter
    def cast_shadows(self, value):
        raise NotImplementedError

    @property
    def receive_shadows(self) -> bool:
        raise NotImplementedError

    @receive_shadows.setter
    def receive_shadows(self, value):
        raise NotImplementedError


class Material(IMaterial):
    _allow_init = False

    def __init__(self, name: str, shader: "Shader", prog: moderngl.Program, values: dict, defines: dict, textures: dict[str: Union[moderngl.Texture, moderngl.Sampler]], const_keys: set = None, bound_shadowmap_mat=None):
        super().__init__()
        if not Material._allow_init:
            raise Exception("Do not create material using Material.__init__(). Use Shader.create_material() instead")
        self._name = name
        self._shader = shader
        self._prog = prog  # material and material instance share the same prog
        self._defines = defines  # readonly
        self._default_values = values  # readonly
        self._values = copy.deepcopy(values)
        self._textures = textures
        self._shadowmap_mat: Optional["Material"] = bound_shadowmap_mat

        # 初始化prog 的value
        for key, value in self._default_values.items():
            self._prog[key].value = value

        # _CameraDataUBO = self._prog.get("CameraData", None)
        # if _CameraDataUBO:
        #     _CameraDataUBO.binding = 1
        # _LightDataUBO = self._prog.get("LightData", None)
        # if _LightDataUBO:
        #     _LightDataUBO.binding = 2

        if const_keys is None:
            self._const_keys = set()
            self._dynamic_keys = set(self._values.keys())
        else:
            self._const_keys = const_keys
            self._dynamic_keys = set(self._values.keys()) - const_keys

        self._num_instances = 0

        self._cast_shadows: bool = True and self.support_cast_shadow
        self._receive_shadows: bool = True

        self._ui = MaterialUI(self)

    def bind_shadowmap_mat(self, shadow_map_mat):
        self._shadowmap_mat = shadow_map_mat

    def write_mvp(self, m_model, m_camera, m_proj):
        self._prog['m_model'].write(m_model)
        self._prog['m_camera'].write(m_camera)
        self._prog['m_proj'].write(m_proj)

    def write_m(self, m_model):
        self._prog['m_model'].write(m_model)

    @deprecated
    def use(self):
        # only update keys marked as overridden for better performance
        # for key in self._dynamic_keys:
        #     self._prog[key] = self._values[key]
        for key, texture in self.textures.items():
            if texture is not None:
                location = self.values[key]
                texture.use(location)

    def copy(self, name=None) -> "Material":
        if name is None:
            name = f"{self.name}(copied)"
        values = copy.deepcopy(self._values)
        defines = copy.deepcopy(self._defines)
        const_keys = copy.deepcopy(self._const_keys)
        mat = self.shader.create_material(name, values, defines, const_keys)
        return mat

    @property
    def name(self):
        return self._name

    @property
    def shader(self):
        return self._shader

    @property
    def prog(self):
        return self._prog

    @property
    def values(self):
        return self._values

    @property
    def default_values(self):
        return self._default_values

    @property
    def defines(self):
        return self._defines

    @property
    def textures(self):
        return self._textures

    def set_texture(self, name, texture: Union[moderngl.Texture, moderngl.Sampler]):
        if name not in self.textures:
            return
        self._textures[name] = texture

    @property
    def dynamic_keys(self):
        return self._dynamic_keys

    @property
    def shadowmap_mat(self) -> "Material":
        return self._shadowmap_mat

    @property
    def cast_shadows(self):
        return self._cast_shadows

    @cast_shadows.setter
    def cast_shadows(self, value):
        if not self.support_cast_shadow:
            return
        self._cast_shadows = value

    @property
    def receive_shadows(self):
        return self._receive_shadows

    @receive_shadows.setter
    def receive_shadows(self, value):
        if not self.support_receive_shadow:
            return
        self._receive_shadows = value

    def __getitem__(self, key):
        return self._values[key]

    def __setitem__(self, key, value):
        if key not in self.dynamic_keys:
            logging.error(f"Key {key} is marked as constant or not assigned. Material: {self.name}")
            raise Exception
        self._values[key] = value
        self._prog[key] = value
        # 同步给关联的shadowmap material
        if self._shadowmap_mat is not None and key in self._shadowmap_mat.dynamic_keys:
            self._shadowmap_mat[key] = value

    @deprecated(version='1.0', reason="This method is deprecated, Material Instance is no longer supported.")
    def create_instance(self):
        instance = MaterialInstance(self, self._num_instances)
        self._num_instances += 1
        return instance

    @cached_property
    def support_m(self) -> bool:
        return support_m(self._prog)

    @cached_property
    def support_mvp(self) -> bool:
        """是否支持mvp"""
        return support_mvp(self._prog)

    @cached_property
    def support_cast_shadow(self) -> bool:
        return support_cast_shadows(self._prog)

    @cached_property
    def support_receive_shadow(self) -> bool:
        """是否支持接收阴影"""
        return True  # TODO

    def operation_panel(self):
        if self._ui:
            return self._ui.operation_panel()
        else:
            return None


@deprecated(version='1.0', reason="This class is deprecated, please use Material only.")
class MaterialInstance(IMaterial):
    def __init__(self, material: Material, idx=-1):
        super().__init__()
        self._name = f"{material.name}(Instance)"
        if idx > 0:
            self._name += f"({idx})"
        self._parent = material
        self._shader = material.shader
        self._prog = material.prog
        self._defines = material.defines
        self._default_values = material.default_values
        self._values = copy.deepcopy(material.values)
        self._shadowmap_mat: Optional[IMaterial] = self._parent.shadowmap_mat.create_instance() if self._parent.shadowmap_mat is not None else None

        self._cast_shadows = self._parent.cast_shadows
        self._receive_shadows = self._parent.receive_shadows

        self._ui = MaterialUI(self)

    def write_mvp(self, m_model, m_camera, m_proj):
        self._prog['m_model'].write(m_model)
        self._prog['m_camera'].write(m_camera)
        self._prog['m_proj'].write(m_proj)

    def write_m(self, m_model):
        self._prog['m_model'].write(m_model)

    def use(self):
        # only update keys marked as dynamic
        for key in self._parent.dynamic_keys:
            self._prog[key] = self._values[key]

    def copy(self):
        return self._parent.create_instance()

    @property
    def name(self):
        return self._name

    @property
    def shader(self):
        return self._shader

    @property
    def prog(self):
        return self._prog

    @property
    def values(self):
        return self._values

    @property
    def default_values(self):
        return self._default_values

    @property
    def defines(self):
        return self._defines

    @property
    def dynamic_keys(self):
        return self._parent.dynamic_keys

    @property
    def shadowmap_mat(self):
        return self._shadowmap_mat

    @property
    def cast_shadows(self):
        return self._cast_shadows

    @cast_shadows.setter
    def cast_shadows(self, value):
        if not self.support_cast_shadow:
            return
        self._cast_shadows = value

    @property
    def receive_shadows(self):
        return self._receive_shadows

    @receive_shadows.setter
    def receive_shadows(self, value):
        if not self.support_receive_shadow:
            return
        self._receive_shadows = value

    def __getitem__(self, key):
        return self._values[key]

    def __setitem__(self, key, value):
        if key not in self.dynamic_keys:
            logging.error(f"Key {key} is marked as constant or not assigned. Material: {self.name}")
        self._values[key] = value

        # 同步给关联的shadowmap material
        if self._shadowmap_mat is not None and key in self.shadowmap_mat.dynamic_keys:
            self._shadowmap_mat[key] = value

    def operation_panel(self):
        if self._ui:
            return self._ui.operation_panel()
        else:
            return None

    @cached_property
    def support_m(self) -> bool:
        return self._parent.support_m

    @cached_property
    def support_mvp(self) -> bool:
        return self._parent.support_mvp

    @cached_property
    def support_cast_shadow(self) -> bool:
        return self._parent.support_cast_shadow

    @cached_property
    def support_receive_shadow(self) -> bool:
        return True  # TODO
