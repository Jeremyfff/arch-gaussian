import time

import imgui
import moderngl
from pyrr import Vector3

from gui.components import c
from gui.global_app_state import g
from gui.modules import GraphicModule, EventModule, StyleModule
from gui.windows.base_window import PopupWindow


class TextureViewerWindow(PopupWindow):
    _name = 'TextureViewerWindow'

    _cached_keys = []
    _selected_simple_tex_idx = -1
    _selected_fbt_idx = -1

    @classmethod
    def w_init(cls):
        super().w_init()

    @classmethod
    def w_update(cls):
        super().w_update()

    @classmethod
    def w_open(cls):
        super().w_open()
        EventModule.register_mouse_scroll_callback(cls._on_mouse_scroll)

    @classmethod
    def w_close(cls):
        super().w_close()
        EventModule.unregister_mouse_scroll_callback(cls._on_mouse_scroll)

    @classmethod
    def w_content(cls):
        super().w_content()

        if imgui.begin_tab_bar("tex_viewer_tab_bar"):
            if imgui.begin_tab_item("FrameBufferTextures").selected:
                cls.fbt_content()
                imgui.end_tab_item()

            if imgui.begin_tab_item("SimpleTextures").selected:
                cls.simple_texture_content()
                imgui.end_tab_item()

            imgui.end_tab_bar()

        # imgui.text('put any texture into g.mSharedTexture to quick view')
        # imgui.text("this is only for debug purpose")
        # if g.mSharedTexture is None:
        #     return
        # imgui.image(g.mSharedTexture.glo, g.mSharedTexture.width, g.mSharedTexture.height)

    @classmethod
    def simple_texture_content(cls):
        imgui.push_id("texture_viewer_window.simple_texture_content")
        width = imgui.get_content_region_available_width()
        c.begin_child("tex_viewer_left", width * 0.3)
        for i, simple_tex in enumerate(GraphicModule.registered_simple_textures):
            clicked, selected = imgui.selectable(simple_tex.name, i == cls._selected_simple_tex_idx)
            if clicked and cls._selected_simple_tex_idx != i:
                cls._selected_simple_tex_idx = i
                cls._cached_scale_ratio.clear()
                cls._cached_img_offset.clear()

        imgui.end_child()
        imgui.same_line()
        c.begin_child("tex_viewer_right")
        width = imgui.get_content_region_available_width()
        if 0 <= cls._selected_simple_tex_idx < len(GraphicModule.registered_simple_textures):
            simple_tex = GraphicModule.registered_simple_textures[cls._selected_simple_tex_idx]
            c.bold_text(simple_tex.name)
            texture = simple_tex.texture
            cls._image_viewer_component("simple_tex viewer", texture, height=width * 0.5)

        imgui.end_child()
        imgui.pop_id()

    @staticmethod
    def last_render_time_to_color(curr_time, lst_render_time):
        if lst_render_time == -1:
            status_color = StyleModule.COLOR_DARK_GRAY
        elif curr_time - lst_render_time < 1.0:
            status_color = StyleModule.COLOR_SUCCESS
        else:
            status_color = StyleModule.COLOR_WARNING
        return status_color

    @classmethod
    def fbt_content(cls):
        imgui.push_id("texture_viewer_window.fbt_content")
        width = imgui.get_content_region_available_width()

        c.begin_child("tex_viewer_left", width * 0.3)
        curr_time = time.time()
        for i, tex in enumerate(GraphicModule.registered_frame_buffer_textures):
            lst_render_time = tex.last_render_time
            status_color = cls.last_render_time_to_color(curr_time, lst_render_time)
            c.icon_image("checkbox-blank-circle-fill", tint_color=status_color, width=g.font_size, height=g.font_size)
            imgui.same_line()
            clicked, selected = imgui.selectable(tex.name, i == cls._selected_fbt_idx)
            if clicked and cls._selected_fbt_idx != i:
                cls._selected_fbt_idx = i
                cls._cached_scale_ratio.clear()
                cls._cached_img_offset.clear()

        imgui.end_child()
        imgui.same_line()
        c.begin_child("tex_viewer_right")
        width = imgui.get_content_region_available_width()
        if 0 <= cls._selected_fbt_idx < len(GraphicModule.registered_frame_buffer_textures):
            fbt = GraphicModule.registered_frame_buffer_textures[cls._selected_fbt_idx]
            c.bold_text(fbt.name)
            imgui.separator()
            lst_render_time = fbt.last_render_time
            status_color = cls.last_render_time_to_color(curr_time, lst_render_time)
            c.icon_image("checkbox-blank-circle-fill", tint_color=status_color, width=g.font_size, height=g.font_size)
            imgui.same_line()
            imgui.text(f"Last Render Time: {fbt.last_render_time: .1f}, Class: {fbt.__class__.__name__}")

            imgui.separator()
            imgui.text("Color Attachment")

            color_attachment = fbt.fbo.color_attachments[0]
            cls._image_viewer_component("color_attachment viewer", color_attachment, height=width * 0.5)

            imgui.separator()
            imgui.text("Depth Attachment")
            if fbt.with_depth:

                depth_attachment = fbt.fbo.depth_attachment
                cls._image_viewer_component("depth_attachment viewer", depth_attachment, height=width * 0.5)
            else:
                c.text("no depth attachment", True)
        imgui.end_child()
        imgui.pop_id()

    _cached_scale_ratio = {}
    _cached_img_offset = {}
    _show_img_border = True

    @classmethod
    def _image_viewer_component(cls, name, tex: moderngl.Texture, width=None, height=None):
        imgui.push_id(name)
        if width is None or height is None:
            w, h = imgui.get_content_region_available()
            if width is None:
                width = w
            if height is None:
                height = h

        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, (0, 0))
        c.begin_child(name, width, height, border=True, flags=imgui.WINDOW_NO_SCROLL_WITH_MOUSE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_SCROLLBAR)

        region_width, region_height = imgui.get_content_region_available()

        if name not in cls._cached_scale_ratio:
            scale_ratio1 = region_width / tex.width
            scale_ratio2 = region_height / tex.height
            scale_ratio = min(scale_ratio1, scale_ratio2) * 0.95
            cls._cached_scale_ratio[name] = scale_ratio
        scale_ratio = cls._cached_scale_ratio[name]
        scale_ratio = max(0.1, scale_ratio)
        scale_ratio = min(20.0, scale_ratio)
        cls._cached_scale_ratio[name] = scale_ratio

        display_width, display_height = int(tex.width * scale_ratio), int(tex.height * scale_ratio)

        center_cursor_pos = ((region_width - display_width) / 2, (region_height - display_height) / 2)
        # center_cursor_pos = ((display_width - region_width) / 2, (display_height - region_height) / 2)
        if name not in cls._cached_img_offset:
            cls._cached_img_offset[name] = Vector3((0, 0, 0))
        offset: Vector3 = cls._cached_img_offset[name]

        imgui.set_cursor_pos((center_cursor_pos[0] + offset.x, center_cursor_pos[1] + offset.y))
        # imgui.set_scroll_x(center_cursor_pos[0] + offset.x)
        # imgui.set_scroll_y(center_cursor_pos[1] + offset.y)

        imgui.image(tex.glo, display_width, display_height, border_color=(1, 1, 1, 1) if cls._show_img_border else (0, 0, 0, 0))

        imgui.end_child()
        imgui.pop_style_var()
        imgui.text(f"width: {tex.width}, height: {tex.height}, channel: {tex.components}")

        imgui.text(f"scale: {scale_ratio:.1f}")
        imgui.same_line()
        if imgui.button("zoom+"):
            cls._cached_scale_ratio[name] *= 1.2
        imgui.same_line()
        if imgui.button("zoom-"):
            cls._cached_scale_ratio[name] /= 1.2
        imgui.same_line()
        if imgui.button("1:1"):
            cls._cached_scale_ratio[name] = 1.0
        imgui.same_line()
        if imgui.arrow_button("left", imgui.DIRECTION_LEFT):
            cls._cached_img_offset[name].x += 100
        imgui.same_line()
        if imgui.arrow_button("right", imgui.DIRECTION_RIGHT):
            cls._cached_img_offset[name].x -= 100
        imgui.same_line()
        if imgui.arrow_button("up", imgui.DIRECTION_UP):
            cls._cached_img_offset[name].y += 100
        imgui.same_line()
        if imgui.arrow_button("down", imgui.DIRECTION_DOWN):
            cls._cached_img_offset[name].y -= 100
        imgui.same_line()
        if imgui.button("reset"):
            cls._cached_scale_ratio.pop(name)
            cls._cached_img_offset.pop(name)
        imgui.same_line()
        _, cls._show_img_border = imgui.checkbox("show border", cls._show_img_border)
        imgui.pop_id()

    @classmethod
    def _on_mouse_scroll(cls, x, y):
        cls._scroll_y = y
