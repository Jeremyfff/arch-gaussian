import os

import moderngl
from PIL import Image, ImageDraw, ImageFont

from gui import global_var as g
from gui.utils import color_utils, io_utils

_cached_icons: dict[str: int] = {}  # name : texture id


def get_icon(name):
    if name in _cached_icons:
        return _cached_icons[name]
    img_path = os.path.join(g.GUI_RESOURCES_ROOT, f'icons/light/{name}.png')
    img = Image.open(img_path)
    texture = create_texture_from_image(img)
    _cached_icons[name] = texture.glo
    return texture.glo


def create_texture_from_image(image: Image) -> moderngl.Texture:
    # must be called after NE.set_window_event()
    width, height = image.size
    channels = 3 if image.mode == 'RGB' else 4
    data = image.tobytes()
    texture = g.mWindowEvent.ctx.texture((width, height), channels, data)
    g.mWindowEvent.imgui.register_texture(texture)
    return texture


def update_texture(texture_id, image: Image):
    assert texture_id in g.mWindowEvent.imgui._textures.keys()
    texture: moderngl.Texture = g.mWindowEvent.imgui._textures[texture_id]
    texture.write(image.tobytes())


def remove_texture(texture_id):
    assert texture_id in g.mWindowEvent.imgui._textures.keys()
    g.mWindowEvent.imgui.remove_texture(g.mWindowEvent.imgui._textures[texture_id])


def register_texture(texture):
    g.mWindowEvent.imgui.register_texture(texture)




_font_size = 24
_font = ImageFont.truetype(os.path.join(g.GUI_RESOURCES_ROOT, 'fonts/arial.ttf'), _font_size)  # 使用 Arial 字体，指定字体大小


def generate_character_icon(character):
    if character in _cached_icons:
        return character
    # 定义一个 HSV 颜色值
    ascii_value = ord(character)
    padded_number = str(ascii_value).zfill(1)
    h = float(padded_number[-1]) / 10  # Hue (色相)
    s = 0.8  # Saturation (饱和度)
    v = 0.75  # Value (明度)
    # 将 HSV 颜色转换为 RGB 颜色
    rgb_color = color_utils.hsv_to_rgb(h, s, v)
    # 添加一个值为 255 的 alpha 通道
    rgba_color = (*rgb_color, 255)
    # 添加一个值为 1 的 alpha 通道
    rgba_color = (*rgb_color, 255)

    # 创建一个空白的 32x32 图像
    img = Image.new('RGBA', (32, 32), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 绘制圆角矩形
    draw.rounded_rectangle(((0, 0), (31, 31)), radius=6, fill=rgba_color, outline=None)

    # 在中间写入字母
    text = character
    x = 8
    y = 4
    draw.text((x, y), text, fill='white', font=_font)
    texture = create_texture_from_image(img)
    _cached_icons[character] = texture.glo
    return character


_cached_folder_thumbnails = {}  # {folder_path: dict[file_name: Texture]}


def get_folder_thumbnails(folder_path, icon_size=64, add_mode=False, force_update=False) -> dict:
    if folder_path in _cached_folder_thumbnails and not force_update and not add_mode:
        return _cached_folder_thumbnails[folder_path]
    if force_update and folder_path in _cached_folder_thumbnails.keys():
        glos = [texture.glo for texture in _cached_folder_thumbnails[folder_path].values()]
        for glo in glos:
            remove_texture(glo)  # recycle texture
        _cached_folder_thumbnails[folder_path] = {}
    if folder_path not in _cached_folder_thumbnails.keys():
        _cached_folder_thumbnails[folder_path] = {}

    for file in os.listdir(folder_path):
        if file in _cached_folder_thumbnails[folder_path].keys():
            continue
        file_path = os.path.join(folder_path, file)
        file_path = file_path.replace('/', '\\')
        if not os.path.isfile(file_path):
            continue
        pil_image = io_utils.get_file_thumbnail(file_path, icon_size)
        texture = create_texture_from_image(pil_image)
        _cached_folder_thumbnails[folder_path][file] = texture

    return _cached_folder_thumbnails[folder_path]
