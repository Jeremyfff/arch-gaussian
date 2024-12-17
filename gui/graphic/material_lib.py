# -*- coding: utf-8 -*-
# @Author  : Yiheng Feng
# @Time    : 12/9/2024 8:58 PM
# @Function:
import copy
from typing import Callable

from gui.graphic.material import Shader, Material


class MaterialLib:
    @classmethod
    def _CreateNewMatHelper(cls, _get_default_mat_func: Callable, name, override_values: dict = None, override_defines: dict = None, const_keys: set = None) -> Material:
        _default_mat: Material = _get_default_mat_func()
        _default_shader: Shader = _default_mat.shader
        values = copy.deepcopy(_default_mat.values)
        if override_values:
            values.update(override_values)
        defines = copy.deepcopy(_default_mat.defines)
        if override_defines:
            defines.update(override_defines)
        return _default_shader.create_material(name, values, defines, const_keys)

    # region LineRGBA
    _DefaultShader_Line: Shader = None
    _DefaultMat_LineRGB: Material = None
    _DefaultMat_LineRGBA: Material = None

    @classmethod
    def GetDefaultMat_LineRGBA(cls) -> Material:
        if cls._DefaultShader_Line is None:
            cls._DefaultShader_Line = Shader("programs/line.glsl")

        if cls._DefaultMat_LineRGBA is None:
            cls._DefaultMat_LineRGBA = cls._DefaultShader_Line.create_material(
                name="_DefaultMat_LineRGBA",
                values={
                    "color": (1, 1, 1, 1)
                },
                defines={
                    "USE_RGBA": 1
                }
            )
        return cls._DefaultMat_LineRGBA

    @classmethod
    def GetDefaultMat_LineRGB(cls) -> Material:
        if cls._DefaultShader_Line is None:
            cls._DefaultShader_Line = Shader("programs/line.glsl")
        if cls._DefaultMat_LineRGB is None:
            cls._DefaultMat_LineRGB = cls._DefaultShader_Line.create_material(
                name="_DefaultMat_LineRGB",
                values={
                    "color": (1, 1, 1)
                },
                defines={
                    "USE_RGBA": 0
                }
            )
        return cls._DefaultMat_LineRGB

    # endregion

    # region GridLine
    _DefaultShader_GridLine: Shader = None
    _DefaultMat_GridLine: Material = None

    @classmethod
    def GetDefaultMat_GridLine(cls) -> Material:
        if cls._DefaultShader_GridLine is None:
            cls._DefaultShader_GridLine = Shader("programs/grid_line.glsl")
        if cls._DefaultMat_GridLine is None:
            cls._DefaultMat_GridLine = cls._DefaultShader_GridLine.create_material(
                name="_DefaultMat_GridLine",
                values={
                    "color": (1, 1, 1, 1),
                    "camPosWS": (0, 0, 0),
                    "maxDist": 1.0
                },
                defines={

                }
            )
        return cls._DefaultMat_GridLine

    # endregion

    # region PtCloud
    _DefaultShader_PtCloud: Shader = None
    _DefaultMat_PtCloudRGBA: Material = None
    _DefaultMat_PtCloudRGB: Material = None

    @classmethod
    def GetDefaultMat_PtCloudRGBA(cls) -> Material:
        if cls._DefaultShader_PtCloud is None:
            cls._DefaultShader_PtCloud = Shader("programs/point_cloud.glsl")

        if cls._DefaultMat_PtCloudRGBA is None:
            cls._DefaultMat_PtCloudRGBA = cls._DefaultShader_PtCloud.create_material(
                name="_DefaultMat_PtCloudRGBA",
                values={
                },
                defines={
                    "USE_RGBA": 1
                }
            )
        return cls._DefaultMat_PtCloudRGBA

    @classmethod
    def GetDefaultMat_PtCloudRGB(cls) -> Material:
        if cls._DefaultShader_PtCloud is None:
            cls._DefaultShader_PtCloud = Shader("programs/point_cloud.glsl")

        if cls._DefaultMat_PtCloudRGB is None:
            cls._DefaultMat_PtCloudRGB = cls._DefaultShader_PtCloud.create_material(
                name="_DefaultMat_PtCloudRGB",
                values={
                },
                defines={
                    "USE_RGBA": 0
                }
            )
        return cls._DefaultMat_PtCloudRGB

    # endregion

    # region Lit

    _DefaultShader_Lit: Shader = None
    _DefaultMat_Lit: Material = None

    values_for_lit_phong_01 = {
        "_Color": (1, 1, 1, 1),
        "_Bias": 0.005,
        "_PoissonDistRadiusDiv": 800.0,
    }
    values_for_lit_phong_02 = {
        "_AmbientColor": (0.2, 0.2, 0.2),
        "_DiffuseColor": (0.5, 0.5, 0.5),
        "_SpecularColor": (1, 1, 1),
        "_Shininess": 32.0,
        "_Bias": 0.005,
        "_PoissonDistRadiusDiv": 800.0,
    }
    values_for_lit_phong_03 = {
        "_AmbientColor": (0.2, 0.2, 0.2),
        "_DiffuseColor": (0.5, 0.5, 0.5),
        "_SpecularColor": (1, 1, 1),
        "_Shininess": 32.0,
        "_Bias": 0.005,
        "_PoissonDistRadiusDiv": 800.0,
    }
    @classmethod
    def GetDefaultMat_Lit(cls) -> Material:
        if cls._DefaultShader_Lit is None:
            cls._DefaultShader_Lit = Shader("programs/lit_phong_03.glsl")

        if cls._DefaultMat_Lit is None:
            cls._DefaultMat_Lit = cls._DefaultShader_Lit.create_material(
                name="_DefaultMat_Lit",
                values=cls.values_for_lit_phong_03
            )
        return cls._DefaultMat_Lit

    @classmethod
    def CreateNewMat_Lit(cls, name, override_values: dict = None, override_defines: dict = None, const_keys: set = None) -> Material:
        return cls._CreateNewMatHelper(cls.GetDefaultMat_Lit, name, override_values, override_defines, const_keys)

    # endregion
    # region Unlit

    _DefaultShader_Unlit: Shader = None
    _DefaultMat_Unlit: Material = None

    @classmethod
    def GetDefaultMat_Unlit(cls) -> Material:

        if cls._DefaultShader_Unlit is None:
            cls._DefaultShader_Unlit = Shader("programs/unlit_simple.glsl")

        if cls._DefaultMat_Unlit is None:
            cls._DefaultMat_Unlit = cls._DefaultShader_Unlit.create_material(
                name="_DefaultMat_Unlit",
                values={
                    "_Color": (1, 0, 1, 1),
                    # "_Texture0: 0
                },
                defines={
                    'USE_TEXTURE': 0
                }
            )
        return cls._DefaultMat_Unlit

    @classmethod
    def CreateNewMat_Unlit(cls, name, override_values: dict = None, override_defines: dict = None, const_keys: set = None) -> Material:
        return cls._CreateNewMatHelper(cls.GetDefaultMat_Unlit, name, override_values, override_defines, const_keys)

    # endregion

    # region GaussianColor
    _DefaultShader_GaussianColor: Shader = None
    _DefaultMat_GaussianColor: Material = None

    @classmethod
    def GetDefaultMat_GaussianColor(cls) -> Material:
        if cls._DefaultShader_GaussianColor is None:
            cls._DefaultShader_GaussianColor = Shader("programs/gaussian_color.glsl")
        if cls._DefaultMat_GaussianColor is None:
            cls._DefaultMat_GaussianColor = cls._DefaultShader_GaussianColor.create_material(
                name="_DefaultMat_GaussianColor",
                values={
                    'Tr': 0,
                    'Tg': 1,
                    'Tb': 2,
                    'Ta': 3
                },
                defines={

                }
            )
        return cls._DefaultMat_GaussianColor

    # endregion

    # region GaussianBlender

    _DefaultShader_GaussianBlender: Shader = None

    _DefaultMat_GaussianBlender: Material = None

    @classmethod
    def GetDefaultMat_GaussianBlender(cls) -> Material:
        if cls._DefaultShader_GaussianBlender is None:
            cls._DefaultShader_GaussianBlender = Shader("programs/gaussian_blender.glsl")
        if cls._DefaultMat_GaussianBlender is None:
            cls._DefaultMat_GaussianBlender = cls._DefaultShader_GaussianBlender.create_material(
                name="_DefaultMat_GaussianBlender",
                values={
                    'geometry_color_texture': 0,
                    'gaussian_color_texture': 1,
                }, defines={

                }
            )
        return cls._DefaultMat_GaussianBlender

    # endregion
    # region FullScreen Blur

    _DefaultShader_FSBlur: Shader = None
    _DefaultMat_FSBlur: Material = None

    @classmethod
    def GetDefaultMat_FSBlur(cls) -> Material:
        if cls._DefaultShader_FSBlur is None:
            cls._DefaultShader_FSBlur = Shader("programs/ui_blur.glsl")
        if cls._DefaultMat_FSBlur is None:
            cls._DefaultMat_FSBlur = cls._DefaultShader_FSBlur.create_material(
                name="_DefaultMat_FSBlur",
                values={
                    '_Texture': 0,
                    '_Dir': (1, 0),
                    '_Radius': 0.0,
                    '_K_Y': 0.0,
                    '_B_Y': 1.0,
                    '_K_X': 0.0,
                    '_B_X': 1.0,
                    '_Tint0': (1, 1, 1, 1),
                    '_Tint1': (1, 1, 1, 1)
                }, defines={

                }
            )
        return cls._DefaultMat_FSBlur

    # endregion

    # region RoundedButton
    _DefaultShader_RoundedButton: Shader = None
    _DefaultMat_RoundedButton: Material = None

    @classmethod
    def GetDefaultMat_RoundedButton(cls) -> Material:
        if cls._DefaultShader_RoundedButton is None:
            cls._DefaultShader_RoundedButton = Shader("programs/rounded_button.glsl")
        if cls._DefaultMat_RoundedButton is None:
            cls._DefaultMat_RoundedButton = cls._DefaultShader_RoundedButton.create_material(
                name="_DefaultMat_RoundedButton",
                values={
                    '_T': 0,
                    '_Resolution': (1, 1),
                    '_Rounding': 0
                },
                defines={

                }
            )
        return cls._DefaultMat_RoundedButton

    # endregion

    # region Chart
    _DefaultShader_Chart: Shader = None
    _DefaultMat_Chart: Material = None

    @classmethod
    def GetDefaultMat_Chart(cls) -> Material:
        if cls._DefaultShader_Chart is None:
            cls._DefaultShader_Chart = Shader("programs/chart.glsl")
        if cls._DefaultMat_Chart is None:
            cls._DefaultMat_Chart = cls._DefaultShader_Chart.create_material(
                name="_DefaultMat_Chart",
                values={
                    '_Resolution': (1, 1),
                    '_DataTex': 0,
                    '_Capacity': 0,
                    '_DataMin': 0,
                    '_DataMax': 0,
                    '_ColorMin': (0.5, 0.5, 0.5, 0.5),
                    '_ColorMax': (1, 1, 1, 1),
                    '_ColorLine': (1, 1, 1, 1),
                    '_NumUndefinedData': 0
                },
                defines={

                }
            )
        return cls._DefaultMat_Chart

    # endregion

    # region ProgressBar
    _DefaultShader_ProgressBar: Shader = None
    _DefaultMat_ProgressBar: Material = None

    @classmethod
    def GetDefaultMat_ProgressBar(cls) -> Material:
        if cls._DefaultShader_ProgressBar is None:
            cls._DefaultShader_ProgressBar = Shader("programs/progress_bar.glsl")
        if cls._DefaultMat_ProgressBar is None:
            cls._DefaultMat_ProgressBar = cls._DefaultShader_ProgressBar.create_material(
                name="_DefaultMat_ProgressBar",
                values={
                    '_T': 0,
                    '_BgColor': (0, 0, 0, 0),
                    '_BarColor': (0, 0, 0, 0),
                    '_Resolution': (1, 1),
                    '_Rounding': 0,
                    '_Progress': 0,
                    '_IsPreparing': 0,
                    '_IsRunning': 0
                },
                defines={

                }
            )
        return cls._DefaultMat_ProgressBar

    # endregion

    # region SkyBox
    _DefaultShader_SkyBox: Shader = None
    _DefaultMat_SkyBox: Material = None

    @classmethod
    def GetDefaultMat_SkyBox(cls) -> Material:
        if cls._DefaultShader_SkyBox is None:
            cls._DefaultShader_SkyBox = Shader("programs/skybox.glsl")
        if cls._DefaultMat_SkyBox is None:
            cls._DefaultMat_SkyBox = cls._DefaultShader_SkyBox.create_material(
                name="_DefaultMat_SkyBox",
                values={
                    "_LightDir": (1, 0, 0),
                    "_GroundColor": (0.37, 0.35, 0.34),
                    "_WaveLengthColor": (1 - 1.0 / 5.60204474633241, 1 - 1.0 / 9.4732844379203038, 1 - 1.0 / 19.643802610477206)
                },
                defines={

                }
            )
        return cls._DefaultMat_SkyBox

    # endregion
