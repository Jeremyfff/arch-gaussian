from typing import Callable

from gui.modules.base_module import BaseModule

__runtime__ = True
if not __runtime__:
    from gui.graphic.geometry_collection import SceneTime


class EventModule(BaseModule):
    # event callback set
    _resize_callbacks = set()
    _key_event_callbacks = set()
    _mouse_position_callbacks = set()
    _mouse_drag_callbacks = set()
    _mouse_scroll_smooth_callbacks = set()
    _mouse_scroll_callbacks = set()
    _mouse_press_callbacks = set()
    _mouse_release_callbacks = set()
    _unicode_char_entered_callbacks = set()
    _files_dropped_callbacks = set()
    _ready_to_close_callbacks = set()

    @classmethod
    def m_init(cls):
        super().m_init()

    @classmethod
    def register_resize_callback(cls, func: Callable[[int, int], None]):
        cls._resize_callbacks.add(func)

    @classmethod
    def unregister_resize_callback(cls, func):
        cls._resize_callbacks.remove(func)

    @classmethod
    def resize(cls, width: int, height: int):
        for func in cls._resize_callbacks:
            func(width, height)

    @classmethod
    def register_key_event_callback(cls, func: Callable[[any, any, any], None]):
        cls._key_event_callbacks.add(func)

    @classmethod
    def unregister_key_event_callback(cls, func):
        cls._key_event_callbacks.remove(func)

    @classmethod
    def key_event(cls, key, action, modifiers):
        for func in cls._key_event_callbacks:
            func(key, action, modifiers)

    @classmethod
    def register_mouse_position_callback(cls, func: Callable[[int, int, int, int], None]):
        cls._mouse_position_callbacks.add(func)

    @classmethod
    def unregister_mouse_position_callback(cls, func):
        cls._mouse_position_callbacks.remove(func)

    @classmethod
    def mouse_position_event(cls, x: int, y: int, dx: int, dy: int):
        for func in cls._mouse_position_callbacks:
            func(x, y, dx, dy)

    @classmethod
    def register_mouse_drag_callback(cls, func: Callable[[int, int, int, int], None]):
        cls._mouse_drag_callbacks.add(func)

    @classmethod
    def unregister_mouse_drag_callback(cls, func):
        cls._mouse_drag_callbacks.remove(func)

    @classmethod
    def mouse_drag_event(cls, x: int, y: int, dx: int, dy: int):
        for func in cls._mouse_drag_callbacks:
            func(x, y, dx, dy)

    @classmethod
    def register_mouse_scroll_smooth_callback(cls, func: Callable[[float, float], None]):
        cls._mouse_scroll_smooth_callbacks.add(func)

    @classmethod
    def unregister_mouse_scroll_smooth_callback(cls, func):
        cls._mouse_scroll_smooth_callbacks.remove(func)

    @classmethod
    def mouse_scroll_event_smooth(cls, x_offset: float, y_offset: float):
        for func in cls._mouse_scroll_smooth_callbacks:
            func(x_offset, y_offset)

    @classmethod
    def register_mouse_scroll_callback(cls, func: Callable[[int, int], None]):
        cls._mouse_scroll_callbacks.add(func)

    @classmethod
    def unregister_mouse_scroll_callback(cls, func):
        cls._mouse_scroll_callbacks.remove(func)

    @classmethod
    def mouse_scroll_event(cls, x_offset: int, y_offset: int):
        for func in cls._mouse_scroll_callbacks:
            func(x_offset, y_offset)

    @classmethod
    def register_mouse_press_callback(cls, func: Callable[[int, int, int], None]):
        cls._mouse_press_callbacks.add(func)

    @classmethod
    def unregister_mouse_press_callback(cls, func):
        cls._mouse_press_callbacks.remove(func)

    @classmethod
    def mouse_press_event(cls, x: int, y: int, button: int):
        for func in cls._mouse_press_callbacks:
            func(x, y, button)

    @classmethod
    def register_mouse_release_callback(cls, func: Callable[[int, int, int], None]):
        cls._mouse_release_callbacks.add(func)

    @classmethod
    def unregister_mouse_release_callback(cls, func):
        cls._mouse_release_callbacks.remove(func)

    @classmethod
    def mouse_release_event(cls, x: int, y: int, button: int):
        for func in cls._mouse_release_callbacks:
            func(x, y, button)

    @classmethod
    def register_unicode_char_entered_callback(cls, func: Callable[[str], None]):
        cls._unicode_char_entered_callbacks.add(func)

    @classmethod
    def unregister_unicode_char_entered_callback(cls, func):
        cls._unicode_char_entered_callbacks.remove(func)

    @classmethod
    def unicode_char_entered(cls, char: str):
        for func in cls._unicode_char_entered_callbacks:
            func(char)

    @classmethod
    def register_files_dropped_callback(cls, func: Callable[[int, int, list], None]):
        cls._files_dropped_callbacks.add(func)

    @classmethod
    def unregister_files_dropped_callback(cls, func):
        cls._files_dropped_callbacks.remove(func)

    @classmethod
    def files_dropped_event(cls, x: int, y: int, paths: list):
        for func in cls._files_dropped_callbacks:
            func(x, y, paths)

    @classmethod
    def register_ready_to_close_callback(cls, func: Callable[[], None]):
        cls._ready_to_close_callbacks.add(func)

    @classmethod
    def unregister_ready_to_close_callback(cls, func):
        cls._ready_to_close_callbacks.remove(func)

    @classmethod
    def ready_to_close(cls):
        for func in cls._ready_to_close_callbacks:
            func()

    _nav_idx_change_callbacks = set()

    @classmethod
    def register_nav_idx_change_callback(cls, func: Callable[[int, int], None]):
        cls._nav_idx_change_callbacks.add(func)

    @classmethod
    def unregister_nav_idx_change_callback(cls, func):
        cls._nav_idx_change_callbacks.remove(func)

    @classmethod
    def on_nav_idx_changed(cls, org_idx: int, idx: int):
        for func in cls._nav_idx_change_callbacks:
            func(org_idx, idx)

    _scene_manager_change_callbacks = set()

    @classmethod
    def register_scene_manager_change_callback(cls, func: Callable):
        cls._scene_manager_change_callbacks.add(func)

    @classmethod
    def unregister_scene_manager_change_callback(cls, func):
        cls._scene_manager_change_callbacks.remove(func)

    @classmethod
    def on_scene_manager_changed(cls, scene_manager):
        for func in cls._scene_manager_change_callbacks:
            func(scene_manager)

    _gaussian_manager_change_callbacks = set()

    @classmethod
    def register_gaussian_manager_change_callback(cls, func: Callable):
        cls._gaussian_manager_change_callbacks.add(func)

    @classmethod
    def unregister_gaussian_manager_change_callback(cls, func):
        cls._gaussian_manager_change_callbacks.remove(func)

    @classmethod
    def on_gaussian_manager_changed(cls, gaussian_manager):
        for func in cls._gaussian_manager_change_callbacks:
            func(gaussian_manager)

    _camera_manager_change_callbacks = set()

    @classmethod
    def register_camera_manager_change_callback(cls, func: Callable):
        cls._camera_manager_change_callbacks.add(func)

    @classmethod
    def unregister_camera_manager_change_callback(cls, func):
        cls._camera_manager_change_callbacks.remove(func)

    @classmethod
    def on_camera_manager_changed(cls, camera_manager):
        for func in cls._camera_manager_change_callbacks:
            func(camera_manager)

    _get_depth_callbacks = set()

    @classmethod
    def register_get_depth_callback(cls, func: Callable):
        cls._get_depth_callbacks.add(func)

    @classmethod
    def unregister_get_depth_callback(cls, func):
        cls._get_depth_callbacks.remove(func)

    @classmethod
    def on_get_depth(cls, geo_depth, geo_target, gaussian_depth, gaussian_target):
        """几何体距离， 几何体目标点， 高斯距离， 高斯目标点， 综合距离， 综合目标点"""
        for func in cls._get_depth_callbacks:
            func(geo_depth, geo_target, gaussian_depth, gaussian_target)

    _project_changed_callbacks = set()

    @classmethod
    def register_project_change_callback(cls, func: Callable):
        cls._project_changed_callbacks.add(func)

    @classmethod
    def unregister_project_change_callback(cls, func):
        cls._project_changed_callbacks.remove(func)

    @classmethod
    def on_project_change(cls):
        for func in cls._project_changed_callbacks:
            func()

    _progress_ctx_callbacks = set()

    @classmethod
    def register_progress_ctx_change_callback(cls, func: Callable):
        cls._progress_ctx_callbacks.add(func)

    @classmethod
    def unregister_progress_ctx_change_callback(cls, func: Callable):
        cls._progress_ctx_callbacks.remove(func)

    @classmethod
    def on_progress_ctx_change(cls):
        for func in cls._progress_ctx_callbacks:
            func()

    _bg_style_change_callbacks = set()

    @classmethod
    def register_bg_style_change_callback(cls, func: Callable):
        cls._bg_style_change_callbacks.add(func)

    @classmethod
    def unregister_bg_style_change_callback(cls, func: Callable):
        cls._bg_style_change_callbacks.remove(func)

    @classmethod
    def on_bg_style_change(cls):
        for func in cls._bg_style_change_callbacks:
            func()

    _global_scale_change_callbacks = set()

    @classmethod
    def register_global_scale_change_callback(cls, func: Callable):
        if func not in cls._global_scale_change_callbacks:
            cls._global_scale_change_callbacks.add(func)

    @classmethod
    def unregister_global_scale_change_callback(cls, func: Callable):
        if func in cls._global_scale_change_callbacks:
            cls._global_scale_change_callbacks.remove(func)

    @classmethod
    def on_global_scale_change(cls):
        for func in cls._global_scale_change_callbacks:
            func()

    _language_change_callbacks = set()

    @classmethod
    def register_language_change_callback(cls, func: Callable):
        cls._language_change_callbacks.add(func)

    @classmethod
    def unregister_language_change_callback(cls, func: Callable):
        cls._language_change_callbacks.remove(func)

    @classmethod
    def on_language_change(cls):
        for func in cls._language_change_callbacks:
            func()

    _scene_time_change_callbacks = set()

    @classmethod
    def register_scene_time_change_callback(cls, func: Callable[["SceneTime"], None]):
        cls._scene_time_change_callbacks.add(func)

    @classmethod
    def unregister_scene_time_change_callback(cls, func: Callable[["SceneTime"], None]):
        cls._scene_time_change_callbacks.remove(func)

    @classmethod
    def on_scene_time_change(cls, scene_time: "SceneTime"):
        for func in cls._scene_time_change_callbacks:
            func(scene_time)

