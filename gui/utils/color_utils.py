import colorsys
import math
from typing import Tuple

import numba


def hsv_to_rgb(h, s, v):
    rgb_color = colorsys.hsv_to_rgb(h, s, v)
    return tuple(int(round(c * 255)) for c in rgb_color)


def align_alpha(color1, color2):
    # aline color1's alpha to color2's alpha
    return color1[0], color1[1], color1[2], color1[3] * color2[3]


def set_alpha(color, alpha):
    return color[0], color[1], color[2], alpha


def lighten_color(color, intensity):
    return min(color[0] + intensity, 1), min(color[1] + intensity, 1), min(color[2] + intensity, 1), min(
        color[3] + intensity, 1)


def darken_color(color, intensity):
    return max(color[0] - intensity, 0), max(color[1] - intensity, 0), max(color[2] - intensity, 0), max(
        color[3] + intensity, 0)


# https://github.com/esemeniuc/kelvin_rgb
#  Neil Bartlett
#  neilbartlett.com
#  2015-01-22
#
#  Copyright [2015] [Neil Bartlett] for Javascript source
#  Copyright Eric Semeniuc
#
# Color Temperature is the color due to black body radiation at a given
# temperature. The temperature is given in Kelvin. The concept is widely used
# in photography and in tools such as f.lux.
#
# The function here converts a given color temperature into a near equivalent
# in the RGB colorspace. The function is based on a curve fit on standard sparse
# set of Kelvin to RGB mappings.
#
# NOTE The approximations used are suitable for photo-manipulation and other
# non-critical uses. They are not suitable for medical or other high accuracy
# use cases.
#
# Accuracy is best between 1000K and 40000K.
#
# See http://github.com/neilbartlett/color-temperature for further details.

'''
 A more accurate version algorithm based on a different curve fit to the
 original RGB to Kelvin data.
 Input: color temperature in degrees Kelvin
 Output: tuple of red, green and blue components of the Kelvin temperature
'''


@numba.jit
def __clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    # use rounding to better represent values between max and min
    return max(min(value, max_val), min_val)


# see http://www.zombieprototypes.com/?p=210 for plot and calculation of coefficients
@numba.jit
def k_to_rgb(kelvin: int) -> Tuple[float, float, float]:
    temperature = kelvin / 100.0

    if temperature < 66.0:
        red = 255
    else:
        # a + b x + c Log[x] /.
        # {a -> 351.97690566805693`,
        # b -> 0.114206453784165`,
        # c -> -40.25366309332127
        # x -> (kelvin/100) - 55}
        red = temperature - 55.0
        red = 351.97690566805693 + 0.114206453784165 * red - 40.25366309332127 * math.log(red)

    # Calculate green
    if temperature < 66.0:
        # a + b x + c Log[x] /.
        # {a -> -155.25485562709179`,
        # b -> -0.44596950469579133`,
        # c -> 104.49216199393888`,
        # x -> (kelvin/100) - 2}
        green = temperature - 2
        green = -155.25485562709179 - 0.44596950469579133 * green + 104.49216199393888 * math.log(green)
    else:
        # a + b x + c Log[x] /.
        # {a -> 325.4494125711974`,
        # b -> 0.07943456536662342`,
        # c -> -28.0852963507957`,
        # x -> (kelvin/100) - 50}
        green = temperature - 50.0
        green = 325.4494125711974 + 0.07943456536662342 * green - 28.0852963507957 * math.log(green)

    # Calculate blue
    if temperature >= 66.0:
        blue = 255
    elif temperature <= 20.0:
        blue = 0
    else:
        # a + b x + c Log[x] /.
        # {a -> -254.76935184120902`,
        # b -> 0.8274096064007395`,
        # c -> 115.67994401066147`,
        # x -> kelvin/100 - 10}
        blue = temperature - 10
        blue = -254.76935184120902 + 0.8274096064007395 * blue + 115.67994401066147 * math.log(blue)

    red /= 255.0
    green /= 255.0
    blue /= 255.0
    return __clamp(red, 0, 1), __clamp(green, 0, 1), __clamp(blue, 0, 1)


def k_to_rgb_hex(kelvin: int) -> str:
    return '#%02x%02x%02x' % k_to_rgb(kelvin)
