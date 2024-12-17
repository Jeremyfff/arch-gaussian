import logging
import math
from typing import Optional

import imgui

from gui.components import c
from gui.contents.base_content import BaseContent
from gui.global_app_state import g
from gui.graphic.renderers import IRenderer
from gui.modules import EventModule, DrawingModule, StyleModule
from gui.user_data import user_data

__runtime__ = True
if not __runtime__:
    from src.scene.cameras import Camera


class ViewerContent(BaseContent):
    # ViewerContent同时会维护其渲染器，需要访问渲染器时，可以通过ViewerContent类来访问。
    mRenderer: Optional[IRenderer] = None  # main graphic renderer
    mCameraManager = None

    # misc
    _content_width, _content_height = 0, 0
    _is_content_hovered = False  # is mouse hovering this window
    _is_graphic_renderer_in_hovering_mode = False  # is graphic renderer in hovering mode
    _is_graphic_renderer_in_op_mode = False  # is graphic renderer in operation mode
    _update_graphic_size = False  # update graphic size next frame

    @classmethod
    def c_init(cls):
        super().c_init()
        cls._initialize_renderer()
        cls._update_graphic_size = True  # 初始化时标记需要更新渲染器尺寸

    @classmethod
    def c_update(cls):
        super().c_update()
        cls.mRenderer.update()
        cls.mRenderer.render()

    @classmethod
    def c_show(cls):
        super().c_show()
        cls._content_width, cls._content_height = cls._get_content_size()
        cls._is_content_hovered = imgui.is_window_hovered() and not imgui.is_any_item_hovered()
        if cls._update_graphic_size:
            renderer_width, renderer_height = cls._content_width // user_data.renderer_downsample, cls._content_height // user_data.renderer_downsample
            cls.mRenderer.update_size(renderer_width, renderer_height)
            cls._update_graphic_size = False

        cp = imgui.get_cursor_pos()
        wp = imgui.get_window_position()
        g.mImagePos = (wp[0] + cp[0], wp[1] + cp[1])
        # display image
        imgui.image(cls.mRenderer.texture_id, cls._content_width, cls._content_height, (0, 1), (1, 0))

        # show overlay content
        imgui.set_cursor_pos(cp)
        cls.show_overlay_content()

    @classmethod
    def c_on_show(cls):
        """on content show (this is run under imgui context) """
        super().c_on_show()
        cls._register_events()

    @classmethod
    def c_on_hide(cls):
        """on content hide (this is run under imgui context)"""
        super().c_on_hide()
        cls._unregister_events()

    @staticmethod
    def _get_content_size():
        """获取渲染空间大小"""
        return int(imgui.get_window_width() - 0 * g.mImguiStyle.window_padding[0]), \
            int(imgui.get_window_height() - 0 * g.mImguiStyle.window_padding[1])

    @classmethod
    def show_overlay_content(cls):
        """
        Entry for all overlay contents
        """
        cls.show_tool_bar()
        if user_data.can_show_debug_info:
            cls.show_debug_info()
        if user_data.can_show_help_info:
            cls.show_help_info()

    @classmethod
    def show_tool_bar(cls):
        """the bottom toolbar"""
        org_cursor_pos = imgui.get_cursor_pos()

        imgui.set_cursor_pos_y(imgui.get_window_height() - imgui.get_frame_height_with_spacing())
        wp = imgui.get_window_position()

        button_size = imgui.get_frame_height() * 0.8
        start_pos_x = imgui.get_cursor_pos_x() + wp[0]
        start_pos_y = imgui.get_cursor_pos_y() + wp[1]
        DrawingModule.draw_rect_filled(start_pos_x,
                                       start_pos_y,
                                       cls._content_width + start_pos_x, imgui.get_frame_height_with_spacing() + start_pos_y,
                                       (0.1, 0.1, 0.1, 0.95), 0, 0, "window")
        imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + imgui.get_frame_height() - button_size)
        imgui.push_style_var(imgui.STYLE_FRAME_ROUNDING, 0)
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, (1 * g.global_scale, 0))
        tint_color = StyleModule.COLOR_GRAY if user_data.can_show_debug_info else StyleModule.COLOR_DARK_GRAY
        icon_name = "wrench-fill" if user_data.can_show_debug_info else "wrench"

        if c.icon_button(icon_name, width=button_size, height=button_size, tooltip="Show Debug Info", id="show_debug_info", tint_color=tint_color):
            user_data.can_show_debug_info = not user_data.can_show_debug_info

        imgui.same_line()
        tint_color = StyleModule.COLOR_GRAY if user_data.can_show_help_info else StyleModule.COLOR_DARK_GRAY
        icon_name = "info-circle-fill" if user_data.can_show_help_info else "info-circle"

        if c.icon_button(icon_name, width=button_size, height=button_size, tooltip="Show Help Info", id="show_help_info", tint_color=tint_color):
            user_data.can_show_help_info = not user_data.can_show_help_info

        imgui.same_line()
        tint_color = StyleModule.COLOR_GRAY if user_data.can_print_key_events else StyleModule.COLOR_DARK_GRAY
        icon_name = "shortcut-fill" if user_data.can_print_key_events else "shortcut"
        if c.icon_button(icon_name, width=button_size, height=button_size, tooltip="Print Key Events", id="print_key_events", tint_color=tint_color):
            user_data.can_print_key_events = not user_data.can_print_key_events

        imgui.same_line()
        tint_color = StyleModule.COLOR_GRAY if user_data.can_show_scene_grid else StyleModule.COLOR_DARK_GRAY
        icon_name = "grid"
        if c.icon_button(icon_name, width=button_size, height=button_size, tooltip="Show Grid", id="show_grid", tint_color=tint_color):
            user_data.can_show_scene_grid = not user_data.can_show_scene_grid
            if cls.mRenderer.scene_basic_geometry_collection is not None:
                cls.mRenderer.scene_basic_geometry_collection.set_grid_status(user_data.can_show_scene_grid)

        imgui.same_line()
        tint_color = StyleModule.COLOR_GRAY if user_data.can_show_scene_axis else StyleModule.COLOR_DARK_GRAY
        icon_name = "axis"
        if c.icon_button(icon_name, width=button_size, height=button_size, tooltip="Show Axis", id="show_axis", tint_color=tint_color):
            user_data.can_show_scene_axis = not user_data.can_show_scene_axis
            if cls.mRenderer.scene_basic_geometry_collection is not None:
                cls.mRenderer.scene_basic_geometry_collection.set_axis_status(user_data.can_show_scene_axis)

        imgui.same_line()
        tint_color = StyleModule.COLOR_GRAY if user_data.can_show_skybox else StyleModule.COLOR_DARK_GRAY
        icon_name = "cloudy"
        if c.icon_button(icon_name, width=button_size, height=button_size, tooltip="Show Skybox", id="show_skybox", tint_color=tint_color):
            user_data.can_show_skybox = not user_data.can_show_skybox
            if cls.mRenderer.scene_basic_geometry_collection is not None:
                cls.mRenderer.scene_basic_geometry_collection.set_skybox_status(user_data.can_show_skybox)

        imgui.same_line()
        tint_color = StyleModule.COLOR_GRAY if user_data.can_render_geometry else StyleModule.COLOR_DARK_GRAY
        icon_name = "3d-box"
        if c.icon_button(icon_name, width=button_size, height=button_size, tooltip="Render Geometry", id="render_geometry", tint_color=tint_color):
            user_data.can_render_geometry = not user_data.can_render_geometry

        imgui.same_line()
        tint_color = StyleModule.COLOR_GRAY if user_data.can_render_debug_geometry else StyleModule.COLOR_DARK_GRAY
        icon_name = "debug"
        if c.icon_button(icon_name, width=button_size, height=button_size, tooltip="Render Debug Geometry", id="render_debug_geometry", tint_color=tint_color):
            user_data.can_render_debug_geometry = not user_data.can_render_debug_geometry

        imgui.same_line()
        tint_color = StyleModule.COLOR_GRAY if user_data.can_render_gaussian else StyleModule.COLOR_DARK_GRAY
        icon_name = "point-cloud"
        if c.icon_button(icon_name, width=button_size, height=button_size, tooltip="Render Gaussian", id="render_gaussian", tint_color=tint_color):
            user_data.can_render_gaussian = not user_data.can_render_gaussian

        imgui.same_line()
        tint_color = StyleModule.COLOR_GRAY
        icon_name = "FPS"
        if c.icon_button(icon_name, width=button_size, height=button_size, tooltip="FPS Settings", id="FPS_settings", tint_color=tint_color):
            imgui.open_popup("fps_settings_popup")

        imgui.same_line()
        tint_color = StyleModule.COLOR_GRAY
        icon_name = "geometry"
        if c.icon_button(icon_name, width=button_size, height=button_size, tooltip="Scene Basic Geometry Collection Settings", id="Scene_Basic_Geometry_Collection_Settings", tint_color=tint_color):
            if cls.mRenderer.scene_basic_geometry_collection:
                imgui.open_popup("SBGC_settings_popup")

        imgui.pop_style_var(2)

        if imgui.is_popup_open("fps_settings_popup"):
            imgui.push_style_color(imgui.COLOR_POPUP_BACKGROUND, *g.mImguiStyle.colors[imgui.COLOR_WINDOW_BACKGROUND])
            imgui.set_next_window_position(wp[0], wp[1])
            imgui.set_next_window_size(400 * g.global_scale, imgui.get_window_height() - imgui.get_frame_height_with_spacing())

        if imgui.begin_popup("fps_settings_popup"):
            cls.mRenderer.operation_panel()
            imgui.end_popup()
            imgui.pop_style_color()

        if imgui.is_popup_open("SBGC_settings_popup"):
            imgui.push_style_color(imgui.COLOR_POPUP_BACKGROUND, *g.mImguiStyle.colors[imgui.COLOR_WINDOW_BACKGROUND])
            imgui.set_next_window_position(wp[0], wp[1])
            imgui.set_next_window_size(400 * g.global_scale, imgui.get_window_height() - imgui.get_frame_height_with_spacing())
        if imgui.begin_popup("SBGC_settings_popup"):
            cls.mRenderer.scene_basic_geometry_collection.operation_panel()
            imgui.end_popup()
            imgui.pop_style_color()
        imgui.set_cursor_pos(org_cursor_pos)

    @classmethod
    def show_debug_info(cls):
        c.bold_text(f'[{cls.__name__}]')
        imgui.text(f'_is_graphic_renderer_in_op_mode: {cls._is_graphic_renderer_in_op_mode}')
        imgui.text(f'_is_graphic_renderer_in_hovering_mode: {cls._is_graphic_renderer_in_hovering_mode}')
        if cls.mRenderer is not None:
            cls.mRenderer.show_debug_info()

    @classmethod
    def use_camera(cls, camera: "Camera"):
        FoVy = camera.FoVy
        image_width = camera.image_width
        image_height = camera.image_height
        aspect_ratio = image_width / image_height
        fov = math.degrees(FoVy)
        if cls.mRenderer.width != image_width or cls.mRenderer.height != image_height:
            cls.mRenderer.update_size(image_width, image_height)
        cls.mRenderer.camera.projection.update(aspect_ratio=aspect_ratio, fov=fov)
        cls.mRenderer.camera.update_use_TR(camera.T, camera.R)

    @classmethod
    def show_help_info(cls):
        org_cursor_pos = imgui.get_cursor_pos()

        imgui.set_cursor_pos_y(imgui.get_window_height() - imgui.get_frame_height_with_spacing() * 2)
        icon = "        "
        text = f"{icon} Rotate    {icon}+{icon}Pan    {icon}Zoom"
        text_size = imgui.calc_text_size(text)[0]
        imgui.set_cursor_pos_x((imgui.get_window_width() - text_size) / 2)
        c.icon_image('Right Mouse', padding=True)
        imgui.same_line()
        imgui.text('Rotate    ')
        imgui.same_line()
        c.icon_image('Right Mouse', padding=True)
        imgui.same_line()
        imgui.text('+')
        imgui.same_line()
        c.icon_image('shift-line', padding=True)
        imgui.same_line()
        imgui.text('Pan    ')
        imgui.same_line()
        c.icon_image('Middle Mouse', padding=True)
        imgui.same_line()
        imgui.text('Zoom')
        imgui.set_cursor_pos(org_cursor_pos)

    @classmethod
    def _initialize_renderer(cls):
        cls.mRenderer = IRenderer("DefaultRenderer", 100, 100)
        cls._update_graphic_size = True  # 标记需要更新图形大小

    @classmethod
    def _on_mouse_press(cls, x, y, button):
        _ = x, y
        if not cls._is_content_hovered:
            return
        if button == 2:
            # right mouse button
            cls._enter_view_op_mode(x, y, button)  # enter view op mode when mouse right pressed and hovering window

    @classmethod
    def _on_mouse_release(cls, x, y, button):
        _ = x, y
        if button == 2:
            # right mouse button
            cls._exit_view_op_mode(x, y, button)

    @classmethod
    def _on_mouse_move(cls, x, y, dx, dy):
        _ = x, y, dx, dy
        if cls._is_content_hovered and not cls._is_graphic_renderer_in_hovering_mode:
            cls._enter_view_hovering_mode()
        elif (not cls._is_content_hovered) and cls._is_graphic_renderer_in_hovering_mode and \
                (not cls._is_graphic_renderer_in_op_mode):
            # 没有在画面上，并且不在op mode的时候才会退出view hovering mode， 否则将会等待退出op mode的时候再退出
            cls._exit_view_hovering_mode()

    @classmethod
    def _on_resize(cls, width, height):
        _ = width, height
        cls._update_graphic_size = True  # show() func will handle it

    @classmethod
    def _on_key_event(cls, key, action, modifiers):
        if user_data.can_print_key_events:
            print(key, action, modifiers)

    @classmethod
    def _on_scene_manager_changed(cls, scene_manager):
        from src.manager.scene_manager import SceneManager
        scene_manager: SceneManager = scene_manager
        cls.mRenderer.set_points_arr(scene_manager.scene_info.point_cloud.points,
                                     scene_manager.scene_info.point_cloud.colors)

    @classmethod
    def _on_gaussian_manager_changed(cls, gaussian_manager):
        from src.manager.gaussian_manager import GaussianManager
        gm: GaussianManager = gaussian_manager
        cls.mRenderer.set_gaussian_manager(gm)

    @classmethod
    def _on_camera_manager_changed(cls, camera_manager):
        from src.manager.camera_manager import CameraManager
        cm: CameraManager = camera_manager
        logging.info('on camera manager changed')
        cls.mCameraManager = cm

    @classmethod
    def _register_events(cls):
        # this happened on show
        logging.info(f'[{__name__}] events registered')
        EventModule.register_mouse_press_callback(cls._on_mouse_press)
        EventModule.register_resize_callback(cls._on_resize)
        EventModule.register_mouse_release_callback(cls._on_mouse_release)
        EventModule.register_mouse_position_callback(cls._on_mouse_move)
        EventModule.register_key_event_callback(cls._on_key_event)
        EventModule.register_scene_manager_change_callback(cls._on_scene_manager_changed)
        EventModule.register_gaussian_manager_change_callback(cls._on_gaussian_manager_changed)
        EventModule.register_camera_manager_change_callback(cls._on_camera_manager_changed)

    @classmethod
    def _unregister_events(cls):
        # this happened on hide
        logging.info(f'[{__name__}] events unregistered')
        EventModule.unregister_mouse_press_callback(cls._on_mouse_press)
        EventModule.unregister_resize_callback(cls._on_resize)
        EventModule.unregister_mouse_release_callback(cls._on_mouse_release)
        EventModule.unregister_mouse_position_callback(cls._on_mouse_move)
        EventModule.unregister_key_event_callback(cls._on_key_event)
        EventModule.unregister_scene_manager_change_callback(cls._on_scene_manager_changed)
        EventModule.unregister_gaussian_manager_change_callback(cls._on_gaussian_manager_changed)
        EventModule.unregister_camera_manager_change_callback(cls._on_camera_manager_changed)

    @classmethod
    def _enter_view_op_mode(cls, x, y, button):
        """enable renderer events"""

        if cls.mRenderer is None:
            return
        if cls._is_graphic_renderer_in_op_mode:
            return
        cls.mRenderer.register_events(x, y, button)
        # g.mWindowEvent.wnd.mouse_exclusivity = True
        cls._is_graphic_renderer_in_op_mode = True

    @classmethod
    def _exit_view_op_mode(cls, x, y, button):
        """disable renderer events"""
        if cls.mRenderer is None:
            return
        if not cls._is_graphic_renderer_in_op_mode:
            return
        cls.mRenderer.unregister_events(x, y, button)
        # g.mWindowEvent.wnd.mouse_exclusivity = False
        cls._is_graphic_renderer_in_op_mode = False
        if cls._is_graphic_renderer_in_hovering_mode and not cls._is_content_hovered:
            cls._exit_view_hovering_mode()

    @classmethod
    def _enter_view_hovering_mode(cls):
        if cls.mRenderer is None:
            return
        if cls._is_graphic_renderer_in_hovering_mode:
            return
        cls.mRenderer.register_hovering_events()
        cls._is_graphic_renderer_in_hovering_mode = True

    @classmethod
    def _exit_view_hovering_mode(cls):
        if cls.mRenderer is None:
            return
        if not cls._is_graphic_renderer_in_hovering_mode:
            return
        cls.mRenderer.unregister_hovering_events()
        cls._is_graphic_renderer_in_hovering_mode = False

    @classmethod
    def on_project_changed(cls):
        cls._initialize_renderer()


EventModule.register_project_change_callback(ViewerContent.on_project_changed)
