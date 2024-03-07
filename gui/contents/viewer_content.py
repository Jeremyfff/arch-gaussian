import logging
from typing import Optional

import imgui

from gui import components as c
from gui import global_var as g
from gui.contents.base_content import BaseContent
from gui.graphic.renderers import SceneInfoRenderer
from gui.modules import EventModule


class ViewerContent(BaseContent):
    mRenderer: Optional[SceneInfoRenderer] = None  # main graphic renderer
    # debug
    _can_show_debug_tools = True
    _can_show_debug_info = True
    _can_print_key_events = False
    _can_show_help_info = False

    _is_content_hovered = False  # is mouse hovering this window
    _is_graphic_renderer_in_hovering_mode = False  # is graphic renderer in hovering mode
    _is_graphic_renderer_in_op_mode = False  # is graphic renderer in operation mode
    _update_graphic_size = False  # update graphic size next frame

    @classmethod
    def c_init(cls):
        super().c_init()
        # initialize

        cls._initialize_renderer()

        cls._update_graphic_size = True  # update graphic size when shown

    @classmethod
    def c_update(cls):
        super().c_update()
        if cls.mRenderer is not None:
            cls.mRenderer.render()

    @classmethod
    def c_show(cls):
        super().c_show()
        # handle imgui related values
        cls._is_content_hovered = imgui.is_window_hovered() and not imgui.is_any_item_hovered()
        if cls._update_graphic_size and cls.mRenderer is not None:
            cls.mRenderer.update_size(int(imgui.get_window_width() - 2 * g.mImguiStyle.window_padding[0]),
                                      int(imgui.get_window_height() - 2 * g.mImguiStyle.window_padding[1]))
            cls._update_graphic_size = False
        org_cursor_pos = imgui.get_cursor_pos()
        # display image
        if cls.mRenderer is not None:
            imgui.image(cls.mRenderer.texture_id, cls.mRenderer.width, cls.mRenderer.height)
        else:
            text = 'no renderer'
            text_width, text_height = imgui.calc_text_size(text)
            imgui.set_cursor_pos_x(imgui.get_window_width() / 2 - text_width / 2)
            imgui.set_cursor_pos_y(imgui.get_window_height() / 2 - text_height / 2)
            imgui.text(text)
        # show overlay content
        imgui.set_cursor_pos(org_cursor_pos)
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

    @classmethod
    def show_overlay_content(cls):
        _, cls._can_show_debug_tools = imgui.checkbox('show debug tools', cls._can_show_debug_tools)
        if cls._can_show_debug_tools:
            cls.show_debug_tools()
        if cls._can_show_debug_info:
            cls.show_debug_info()
        if cls._can_show_help_info:
            cls.show_help_info()

    @classmethod
    def show_debug_tools(cls):
        imgui.same_line()
        imgui.text('|')
        imgui.same_line()
        _, cls._can_print_key_events = imgui.checkbox('print key events', cls._can_print_key_events)
        imgui.same_line()
        _, cls._can_show_debug_info = imgui.checkbox('show debug info', cls._can_show_debug_info)
        imgui.same_line()
        _, cls._can_show_help_info = imgui.checkbox('help info', cls._can_show_help_info)

    @classmethod
    def show_debug_info(cls):
        c.bold_text(f'[{cls.__name__}]')
        imgui.text(f'_is_graphic_renderer_in_op_mode: {cls._is_graphic_renderer_in_op_mode}')
        imgui.text(f'_is_graphic_renderer_in_hovering_mode: {cls._is_graphic_renderer_in_hovering_mode}')
        if cls.mRenderer is not None:
            cls.mRenderer.show_debug_info()

    @classmethod
    def show_help_info(cls):
        org_cursor_pos = imgui.get_cursor_pos()

        imgui.set_cursor_pos_y(imgui.get_window_height() - imgui.get_frame_height_with_spacing())
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
        """initialize renderer"""
        logging.info(f'[{__name__}] initialize frame buffer')
        cls.mRenderer = SceneInfoRenderer('test', 100, 100, camera_type='orbit')

    @classmethod
    def _get_content_size(cls):
        # this should be run under imgui context
        return int(imgui.get_window_width() - 2 * g.mImguiStyle.window_padding[0]), \
            int(imgui.get_window_height() - 2 * g.mImguiStyle.window_padding[1])

    @classmethod
    def _on_mouse_press(cls, x, y, button):
        _ = x, y
        if not cls._is_content_hovered:
            return
        if button == 2 or button == 3:
            cls._enter_view_op_mode(x, y, button)  # enter view op mode when mouse right pressed and hovering window

    @classmethod
    def _on_mouse_release(cls, x, y, button):
        _ = x, y
        if button == 2 or button == 3:
            cls._exit_view_op_mode(x, y, button)

    @classmethod
    def _on_mouse_move(cls, x, y, dx, dy):
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
        if cls._can_print_key_events:
            print(key, action, modifiers)

    @classmethod
    def _on_scene_manager_changed(cls, scene_manager):
        from src.manager.scene_manager import SceneManager
        scene_manager: SceneManager = scene_manager
        logging.info('on scene info changed')
        if cls.mRenderer is None:
            logging.info(f'renderer is None. cannot display scene info')
            return
        if type(cls.mRenderer) == SceneInfoRenderer:
            cls.mRenderer.set_points_arr(scene_manager.scene_info.point_cloud.points,
                                         scene_manager.scene_info.point_cloud.colors)

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
