import colorsys


def hsv_to_rgb(h, s, v):
    rgb_color = colorsys.hsv_to_rgb(h, s, v)
    return tuple(int(round(c * 255)) for c in rgb_color)


def align_alpha(color1, color2):
    # aline color1's alpha to color2's alpha
    return color1[0], color1[1], color1[2], color1[3] * color2[3]
