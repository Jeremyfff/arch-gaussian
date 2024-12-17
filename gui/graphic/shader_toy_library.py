import datetime
import math
import uuid

import imgui
import numpy as np
import pytz
from pvlib.solarposition import get_solarposition

from gui.global_app_state import g
from gui.graphic.material import Shader
from gui.modules import StyleModule
from gui.modules.graphic_module import ShaderToyFBT

from gui.utils.transform_utils import get_sun_dir
class Tunnel_OneShader(ShaderToyFBT):
    """
    https://oneshader.net/shader/ffb37ed776
    """

    def __init__(self):
        _shader = Shader("programs/one_shader/planar_light_tunnel.glsl")
        _mat = _shader.create_material(
            name="Mat_Tunnel_OneShader",
            values={
                'iTime': 0,
                'iResolution': (1, 1),
                '_BgColor': (0, 0, 0, 0),
                '_BandSpacing': 0.23,
                '_FrequencyY': 1.73,
                '_SpeedZ': 2.16,
                '_RandomSpeed': 1.73,
                '_FrequencyZ': 0.03,
            },
            defines={

            }
        )
        super().__init__(f"tunnel_{uuid.uuid4()}", 100, 100, _mat)

    def render(self, **kwargs):
        super().render(iTime=g.mTime,
                       iResolution=(self.width, self.height),
                       _BgColor=g.mImguiStyle.colors[imgui.COLOR_WINDOW_BACKGROUND],
                       _BandSpacing=0.23,
                       _FrequencyY=1.73,
                       _SpeedZ=2.16,
                       _RandomSpeed=3.00,
                       _FrequencyZ=0.03
                       )


class Gradient_OneShader(ShaderToyFBT):
    """
    https://oneshader.net/shader/7d773abf5a
    """

    def __init__(self):
        _shader = Shader("programs/one_shader/gradients.glsl")
        _mat = _shader.create_material(
            name="Mat_Gradient_OneShader",
            values={
                "iTime": 0,
                "iResolution": (1, 1),
                "_Temporal": 0.10,
                "_Spatial": 2.00,
                "_GX": 0.0,
                "_GY": 0.1,
                "_GZ": 0.2,
                "_Gradient": 0.3
            },
            defines={

            }
        )
        super().__init__(f"gradient_{uuid.uuid4()}", 100, 100, _mat)

    def render(self, **kwargs):
        super().render(
            iTime=g.mTime,
            iResolution=(self.width, self.height),
            _Temporal=0.10,
            _Spatial=2.00,
            _GX=0.0,
            _GY=0.1,
            _GZ=0.2,
            _Gradient=0.3,
        )


class Podcast_OneShader(ShaderToyFBT):
    """
    https://oneshader.net/shader/016ad917bd
    """

    def __init__(self):
        _shader = Shader("programs/one_shader/podcast.glsl")
        _mat = _shader.create_material(
            name="Mat_Podcast_OneShader",
            values={
                "iTime": 0,
                "_RotZoom": 0.3,
                "_DistStep": 0.01,
                "_Color": (0, 0, 0, 0)
            },
            defines={

            }
        )
        super().__init__(f"podcast{uuid.uuid4()}", 100, 100, _mat)

    def render(self, **kwargs):
        super().render(
            iTime=g.mTime,
            _RotZoom=0.3,
            _DistStep=0.01,
            _Color=StyleModule.COLOR_PRIMARY
        )


class A_Lot_Of_Spheres_OneShader(ShaderToyFBT):
    """
    https://oneshader.net/shader/4258e9f0a4
    """

    def __init__(self):
        _shader = Shader("programs/one_shader/a_lot_of_spheres.glsl")
        _mat = _shader.create_material(
            name="Mat_A_Lot_Of_Spheres_OneShader",
            values={
                'iTime': 0,
                'iResolution': (1, 1)
            },
            defines={

            }
        )
        super().__init__(f"a_lot_of_spheres_{uuid.uuid4()}", 100, 100, _mat)

    def render(self, **kwargs):
        super().render(
            iTime=g.mTime,
            iResolution=(self.width, self.height),
        )


class Facebook_Connect_OneShader(ShaderToyFBT):
    """
    https://oneshader.net/shader/f436cdf20d
    """

    def __init__(self):
        _shader = Shader("programs/one_shader/facebook_connect.glsl")
        _mat = _shader.create_material(
            name="Mat_Facebook_Connect_OneShader",
            values={
                'iTime': 0,
                'iResolution': (1, 1),
                '_Detail': 2.5
            },
            defines={

            }
        )
        super().__init__(f"facebook_connect{uuid.uuid4()}", 100, 100, _mat)

    def render(self, **kwargs):
        super().render(
            iTime=g.mTime,
            iResolution=(self.width, self.height),
            _Detail=2.5,
        )


local_tz = pytz.timezone('Asia/Shanghai')

class AtmosphericScatteringSkyBox_ShaderToy(ShaderToyFBT):
    """
    https://www.shadertoy.com/view/3djSzz
    """

    def __init__(self):
        _shader = Shader("programs/shadertoy/atmospheric_scattering_skybox.glsl")
        _mat = _shader.create_material(
            name="Mat_AtmosphericScatteringSkyBox_ShaderToy",
            values={
                '_LightDir': (0, 0, 1)
            },
            defines={

            }
        )
        super().__init__(f"atmospheric_scattering_skybox_{uuid.uuid4()}", 100, 100, _mat)

    def render(self, **kwargs):
        if 'light_dir' in kwargs:
            light_dir = kwargs['light_dir']
        else:
            # 设置位置信息（纬度、经度、高度）
            latitude = 37.7749
            longitude = -122.4194
            altitude = 10

            # 获取当前时刻
            # time = datetime.datetime.utcnow()

            # 构造春分日的虚拟时间
            h = math.sin(g.mTime) * 6 + 10
            m = (h * 60) % 60

            light_dir = get_sun_dir(latitude,longitude, 2024, 3, 20, int(h), int(m), 0)
        super().render(_LightDir=light_dir)
