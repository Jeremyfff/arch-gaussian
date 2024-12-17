from abc import abstractmethod
from typing import Optional

import imgui
import numpy as np
from moderngl_window.scene.camera import KeyboardCamera

from gui.components import c
from gui.global_app_state import g
from gui.graphic.cameras import GL_3DGS_Camera
from gui.modules import EventModule, CursorModule


class CameraBehaviour:

    def __init__(self):
        self.camera: Optional[GL_3DGS_Camera] = None

    def _key_event(self, key, action, modifiers):
        pass

    def _mouse_position_event(self, x: int, y: int, dx, dy):
        pass

    def _mouse_drag_event(self, x: int, y: int, dx, dy):
        pass

    def _hover_mouse_scroll_event_smooth(self, x_offset: float, y_offset: float):
        pass

    def _hover_key_event(self, key, action, modifiers):
        pass

    def register_events(self, x, y, button):
        _ = x, y, button
        EventModule.register_key_event_callback(self._key_event)
        EventModule.register_mouse_position_callback(self._mouse_position_event)
        EventModule.register_mouse_drag_callback(self._mouse_drag_event)

    def unregister_events(self, x, y, button):
        _ = x, y, button
        EventModule.unregister_key_event_callback(self._key_event)
        EventModule.unregister_mouse_position_callback(self._mouse_position_event)
        EventModule.unregister_mouse_drag_callback(self._mouse_drag_event)

    def register_hovering_events(self):
        EventModule.register_mouse_scroll_smooth_callback(self._hover_mouse_scroll_event_smooth)
        EventModule.register_key_event_callback(self._hover_key_event)

    def unregister_hovering_events(self):
        EventModule.unregister_mouse_scroll_smooth_callback(self._hover_mouse_scroll_event_smooth)
        EventModule.unregister_key_event_callback(self._hover_key_event)

    @abstractmethod
    def update_size(self, width, height):
        raise NotImplementedError

    @abstractmethod
    def show_debug_info(self):
        raise NotImplementedError


# TODO
class FreeCameraBehaviour(CameraBehaviour):
    def __init__(self):
        super().__init__()
        self.camera = KeyboardCamera(g.mWindowEvent.wnd.keys)
        self.camera.projection.update(near=0.1, far=1000)

    def _key_event(self, key, action, modifiers):
        keys = g.mWindowEvent.wnd.keys

        self.camera.key_input(key, action, modifiers)
        if action == keys.ACTION_PRESS:
            if key == 65505:
                # left shift
                self.camera.velocity = 20.0
        elif action == keys.ACTION_RELEASE:
            if key == 65505:
                self.camera.velocity = 10.0

    def _mouse_drag_event(self, x: int, y: int, dx, dy):
        _ = x, y
        if imgui.is_mouse_down(2): return  # middle mouse
        self.camera.rot_state(int(-dx / 10), int(-dy / 10))

    def unregister_events(self, x, y, button):
        super().unregister_events(x, y, button)
        self.camera.move_up(False)
        self.camera.move_down(False)
        self.camera.move_left(False)
        self.camera.move_right(False)
        self.camera.move_forward(False)
        self.camera.move_backward(False)

    def show_debug_info(self):
        super().show_debug_info()
        c.bold_text('[FreeCameraBehaviour]')
        imgui.same_line()
        imgui.text(f'pitch: {self.camera.pitch:.2f} yaw: {self.camera.yaw:.2f} '
                   f'position: {self.camera.position.x:2f} {self.camera.position.y:2f} {self.camera.position.z:2f}'
                   f'fov: {self.camera.projection.fov:.1f} '
                   f'aspect_ratio: {self.camera.projection.aspect_ratio:.2f} '
                   f'near:{self.camera.projection.near:.2f} '
                   f'far{self.camera.projection.far:.1f}')


class OrbitCameraBehaviour(CameraBehaviour):
    def __init__(self, width, height):
        super().__init__()
        self.camera = GL_3DGS_Camera(width, height)

        self.in_pan_mode = False
        self.in_pan_z_mode = False

    def update_size(self, width, height):
        self.camera.update_size(width, height)
        self.camera.update()

    # region Events
    def _mouse_drag_event(self, x: int, y: int, dx, dy):
        _ = x, y
        if self.in_pan_mode:
            # pan mode
            view_matrix = self.camera.matrix
            r = np.array(view_matrix[:3, 0])
            u = np.array(view_matrix[:3, 1])
            delta = (r * -dx + u * dy) * self.camera.mouse_sensitivity * self.camera.radius / 200.0
            self.camera.target = np.array(self.camera.target) + delta
        elif self.in_pan_z_mode:
            # pan z mode
            view_matrix = self.camera.matrix
            f = np.array(view_matrix[:3, 2])
            delta = (f * dy) * self.camera.mouse_sensitivity * self.camera.radius / 200.0
            self.camera.target = np.array(self.camera.target) + delta
        else:
            # normal mode
            self.camera.rot_state(dx * 2, dy * 2)

        self.camera.update()

    def _hover_mouse_scroll_event_smooth(self, x_offset: float, y_offset: float):
        if y_offset == 0:
            return
        self.camera.radius -= y_offset * self.camera.zoom_sensitivity * self.camera.radius / 4.0
        self.camera.radius = max(0.01, self.camera.radius)
        self.camera.update()

    def _hover_key_event(self, key, action, modifiers):
        keys = g.mWindowEvent.wnd.keys
        if action == keys.ACTION_PRESS:
            if key == 65505:
                # left shift
                self._enter_pan_mode()
            if key == 65507:
                # left control
                self._enter_pan_z_mode()
        elif action == keys.ACTION_RELEASE:
            if key == 65505:
                self._exit_pan_mode()
            if key == 65507:
                # left control
                self._exit_pan_z_mode()

    def _enter_pan_mode(self):
        self.in_pan_mode = True
        CursorModule.set_cursor(CursorModule.CursorType.CURSOR_SIZE)

    def _exit_pan_mode(self):
        self.in_pan_mode = False
        CursorModule.set_default_cursor()

    def _enter_pan_z_mode(self):
        self.in_pan_z_mode = True
        CursorModule.set_cursor(CursorModule.CursorType.CURSOR_SIZE_UP_DOWN)

    def _exit_pan_z_mode(self):
        self.in_pan_z_mode = False
        CursorModule.set_default_cursor()

    def unregister_events(self, x, y, button):
        super().unregister_events(x, y, button)

    def unregister_hovering_events(self):
        # 当退出hover mode 的时候
        super().unregister_hovering_events()
        self._exit_pan_mode()
        self._exit_pan_z_mode()

    # endregion

    def show_debug_info(self):
        c.bold_text('[OrbitCameraBehaviour]')
        imgui.indent()
        imgui.text(f'angle_x: {self.camera.angle_x:.1f} '
                   f'angle_y: {self.camera.angle_y:.1f} '
                   f'target: {self.camera.target[0]:.1f},{self.camera.target[1]:.1f},{self.camera.target[2]:.1f} '
                   f'radius: {self.camera.radius:.1f} '
                   f'fov: {self.camera.projection.fov:.1f} '
                   f'ratio: {self.camera.projection.aspect_ratio:.1f} '
                   f'near:{self.camera.projection.near:.2f} '
                   f'far:{self.camera.projection.far:.1f}')
        imgui.text(f'in_pan_mode: {self.in_pan_mode} in_pan_z_mode: {self.in_pan_z_mode}')
        imgui.unindent()

        c.bold_text('[GL_3DGS_Camera]')
        imgui.same_line()
        imgui.text(
            f'P: {self.camera.P} r: {str(self.camera.r)} u: {str(self.camera.u)} f: {str(self.camera.f)}')
