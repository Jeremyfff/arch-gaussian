import colorsys


def hsv_to_rgb(h, s, v):
    rgb_color = colorsys.hsv_to_rgb(h, s, v)
    return tuple(int(round(c * 255)) for c in rgb_color)


def align_alpha(color1, color2):
    # aline color1's alpha to color2's alpha
    return color1[0], color1[1], color1[2], color1[3] * color2[3]


def lighten_color(color, intensity):
    return min(color[0] + intensity, 1), min(color[1] + intensity, 1), min(color[2] + intensity, 1), min(
        color[3] + intensity, 1)


def darken_color(color, intensity):
    return max(color[0] - intensity, 0), max(color[1] - intensity, 0), max(color[2] - intensity, 0), max(
        color[3] + intensity, 0)
