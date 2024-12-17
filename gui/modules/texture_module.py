import hashlib
import os

import moderngl
from PIL import Image, ImageDraw, ImageFont

from gui.global_app_state import g
from gui.global_info import *
from gui.modules import BaseModule
from gui.utils import color_utils, io_utils


class TextureModule(BaseModule):
    _cached_icons: dict[str: moderngl.Texture] = {}  # name : texture id
    _cached_textures: dict[str: moderngl.Texture] = {}  # name: texture

    @classmethod
    def m_init(cls):
        from gui.modules import EventModule
        EventModule.register_global_scale_change_callback(cls._on_global_scale_changed)

    @classmethod
    def get_icon_glo(cls, name, suffix='png') -> int:
        return cls.get_icon(name, suffix).glo

    @classmethod
    def get_icon(cls, name, suffix='png') -> moderngl.Texture:
        """直接从本地resources/icons/文件夹中读取图标"""
        if name in cls._cached_icons:
            return cls._cached_icons[name]
        img_path = os.path.join(RESOURCES_DIR, f'icons/light/{name}.{suffix}')
        img = Image.open(img_path)
        texture = cls.create_texture_from_image(img)
        cls._cached_icons[name] = texture
        return texture

    @classmethod
    def get_texture_glo(cls, name, suffix='png') -> int:
        return cls.get_texture(name, suffix).glo

    @classmethod
    def get_texture(cls, name, suffix="png") -> moderngl.Texture:
        """直接从本地resources/textures/文件夹中读取纹理"""
        if name in cls._cached_textures:
            return cls._cached_textures[name]
        tex_path = os.path.join(RESOURCES_DIR, f"textures/{name}.{suffix}")
        img = Image.open(tex_path)
        texture = cls.create_texture_from_image(img)
        cls._cached_textures[name] = texture
        print(f"create new texture named {name}, id = {texture.glo}")
        return texture

    @classmethod
    def create_texture_from_image(cls, image: Image) -> moderngl.Texture:
        # must be called after NE.set_window_event()
        width, height = image.size
        channels = 3 if image.mode == 'RGB' else 4
        data = image.tobytes()
        texture = g.mWindowEvent.ctx.texture((width, height), channels, data)
        g.mWindowEvent.imgui.register_texture(texture)
        return texture

    @classmethod
    def update_texture(cls, texture_id, image: Image):
        assert texture_id in g.mWindowEvent.imgui._textures.keys()
        texture: moderngl.Texture = g.mWindowEvent.imgui._textures[texture_id]
        texture.write(image.tobytes())

    @classmethod
    def remove_texture(cls, texture_id):
        assert texture_id in g.mWindowEvent.imgui._textures.keys()
        g.mWindowEvent.imgui.remove_texture(g.mWindowEvent.imgui._textures[texture_id])

    @classmethod
    def register_texture(cls, texture):
        g.mWindowEvent.imgui.register_texture(texture)

    _font_size = 48
    _font = ImageFont.truetype(os.path.join(RESOURCES_DIR, 'fonts/arial.ttf'), _font_size)  # 使用 Arial 字体，指定字体大小

    @classmethod
    def generate_character_icon(cls, character):
        if character in cls._cached_icons:
            return character
        # 定义一个 HSV 颜色值
        # ascii_value = ord(character)
        # padded_number = str(ascii_value).zfill(1)
        # h = float(padded_number[-1]) / 10  # Hue (色相)
        # 使用哈希函数生成一个唯一的数值
        hash_value = int(hashlib.sha256(character.encode('utf-8')).hexdigest(), 16)
        # 将哈希值映射到色相范围（0-1）
        h = hash_value % 256 / 255.0
        s = 0.85  # Saturation (饱和度)
        v = 0.80  # Value (明度)
        # 将 HSV 颜色转换为 RGB 颜色
        rgb_color = color_utils.hsv_to_rgb(h, s, v)
        # 添加一个值为 255 的 alpha 通道
        rgba_color = (*rgb_color, 255)

        # 创建一个空白的 32x32 图像
        img = Image.new('RGBA', (64, 64), color=(*rgb_color, 0))
        draw = ImageDraw.Draw(img)

        # 绘制圆角矩形
        draw.rounded_rectangle(((0, 0), (62, 62)), radius=12, fill=rgba_color, outline=None)
        # 在中间写入字母
        text = character
        x = 15
        y = 7
        draw.text((x, y), text, fill='white', font=cls._font)
        texture = cls.create_texture_from_image(img)
        cls._cached_icons[character] = texture
        return character

    cached_folder_thumbnails = {}  # {folder_path: dict[file_name: Texture]}

    @classmethod
    def get_folder_thumbnails(cls, folder_path, icon_size=64, add_mode=False, force_update=False) -> dict:
        if folder_path in cls.cached_folder_thumbnails and not force_update and not add_mode:
            return cls.cached_folder_thumbnails[folder_path]
        if force_update and folder_path in cls.cached_folder_thumbnails.keys():
            glos = [texture.glo for texture in cls.cached_folder_thumbnails[folder_path].values()]
            for glo in glos:
                cls.remove_texture(glo)  # recycle texture
            cls.cached_folder_thumbnails[folder_path] = {}
        if folder_path not in cls.cached_folder_thumbnails.keys():
            cls.cached_folder_thumbnails[folder_path] = {}

        for file in os.listdir(folder_path):
            if file in cls.cached_folder_thumbnails[folder_path].keys():
                continue
            file_path = os.path.join(folder_path, file)
            file_path = file_path.replace('/', '\\')
            if not os.path.isfile(file_path):
                continue
            pil_image = io_utils.get_file_thumbnail(file_path, icon_size)
            texture = cls.create_texture_from_image(pil_image)
            cls.cached_folder_thumbnails[folder_path][file] = texture

        return cls.cached_folder_thumbnails[folder_path]

    @classmethod
    def clear_cache(cls):
        # clear cache
        for key, tex in cls._cached_icons.items():
            tex.release()
            cls.remove_texture(tex.glo)
        cls._cached_icons.clear()
        for key, tex in cls._cached_textures.items():
            tex.release()
            cls.remove_texture(tex.glo)
        cls._cached_textures.clear()

    @classmethod
    def _on_global_scale_changed(cls):
        cls.clear_cache()
