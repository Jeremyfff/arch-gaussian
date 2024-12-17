import logging
from dataclasses import dataclass
from enum import Enum
from typing import Type, Optional, Callable

import imgui
import moderngl

from gui.windows.base_window import BaseWindow, PopupWindow
from gui.windows.bottom_bar_window import BottomBarWindow
from gui.windows.inspector_window import InspectorWindow, GaussianInspectorWindow, GeometryInspectorWindow
from gui.windows.main_window import MainWindow
from gui.windows.nav_bar_window import NavBarWindow
from gui.windows.node_editor_window import NodeEditorWindow
from gui.windows.performance_inspector_window import PerformanceInspectorWindow
from gui.windows.popup_modal_window import ConfirmCloseWindow
from gui.windows.settings_window import SettingsWindow
from gui.windows.texture_viewer_window import TextureViewerWindow
from gui.windows.top_bar_window import TopBarWindow
from gui.windows.progress_window import ProgressWindow

ALL_WINDOWS: list[Type[BaseWindow]] = [
    TopBarWindow,
    BottomBarWindow,
    NavBarWindow,
    MainWindow,
    SettingsWindow,
    TextureViewerWindow,
    InspectorWindow,
    GaussianInspectorWindow,
    GeometryInspectorWindow,
    ConfirmCloseWindow,
    PerformanceInspectorWindow,
    ProgressWindow
]

POPUP_WINDOWS: list[Type[PopupWindow]] = [
    SettingsWindow,
    TextureViewerWindow,
    InspectorWindow,
    GaussianInspectorWindow,
    GeometryInspectorWindow,
    ConfirmCloseWindow,
    PerformanceInspectorWindow,
    ProgressWindow
]

from gui.user_data import user_settings
from gui.modules.graphic_module import FrameBufferTexture, BlurFBT
from gui.modules import ShadowModule
from gui.global_app_state import g


class ExcludeTypes(Enum):
    Nothing = 0
    Self = 1
    AllPopups = 2


@dataclass
class CommandForGetBlurBg:
    caller: Type[PopupWindow]
    exclude_type: ExcludeTypes
    callback: Callable[[moderngl.Texture], None] = None


class WindowManager:
    _tmp_fbt: Optional["FrameBufferTexture"] = None
    _blurred_fbts: dict[Type[PopupWindow]: BlurFBT] = {}  # caller class: blur frame buffer texture
    # commands stack
    _commands: list[CommandForGetBlurBg] = []

    @classmethod
    def w_init(cls):
        # # NOTE: Init All Windows. If your added new windows, make sure to add it into ALL_WINDOWS list.
        for window in ALL_WINDOWS:
            window.w_init()

        _f = user_settings.full_screen_blur_fbt_down_sampling_factor
        cls._tmp_fbt = FrameBufferTexture("copiedFrameBufferTexture", g.mWindowSize[0], g.mWindowSize[1], 3, False)
        cls._fullScreenBlurFrameBufferTexture = BlurFBT("fullScreenBlurFrameBufferTexture", g.mWindowSize[0] // _f, g.mWindowSize[1] // _f, 3)

    @classmethod
    def w_update(cls):
        for window in ALL_WINDOWS:
            window.w_update()

    @classmethod
    def w_render(cls):
        with imgui.font(g.mFont):
            for window in ALL_WINDOWS:
                window.w_show()
        ShadowModule.m_render()  # render shadows

    @classmethod
    def w_late_update(cls):
        while len(cls._commands) > 0:
            cmd: CommandForGetBlurBg = cls._commands.pop()
            cls._execute_blur_cmd(cmd)

    @classmethod
    def request_blurred_bg(cls, caller: Type[PopupWindow], exclude_type: ExcludeTypes, callback: Callable[[moderngl.Texture], None] = None) -> None:
        """
        send instruct to get blurred background, this function will not return anything
        :param caller: caller class, must be a window
        :param exclude_type:
        :param callback: used to receive blurred texture
        :return:
        """
        logging.info(f"[{caller.__name__}] is sending instruct to copy frame")
        cmd = CommandForGetBlurBg(caller, exclude_type, callback)  # create a command
        cls._commands.append(cmd)  # add command to stack, the program will handle it in the late update function

    @classmethod
    def _execute_blur_cmd(cls, cmd: CommandForGetBlurBg):
        g.mIsHandlingBlurCommand = True
        caller = cmd.caller
        exclude_type = cmd.exclude_type
        callback = cmd.callback
        _exclude_windows: set[Type[PopupWindow]] = set()
        if exclude_type == ExcludeTypes.Nothing:
            pass
        elif exclude_type == ExcludeTypes.Self:
            _exclude_windows = {caller}
        elif exclude_type == ExcludeTypes.AllPopups:
            _exclude_windows = set(POPUP_WINDOWS)
        else:
            raise Exception(f"invalid exclude_type {exclude_type}")

        _f = user_settings.full_screen_blur_fbt_down_sampling_factor
        _target_width = g.mWindowSize[0] // _f
        _target_height = g.mWindowSize[1] // _f

        # get target frame buffer texture
        if caller in cls._blurred_fbts.keys():
            _blur_fbt = cls._blurred_fbts[caller]
        else:
            _blur_fbt = BlurFBT(f"_blur_fbt_{caller.__name__}", _target_width, _target_height, 3)
            cls._blurred_fbts[caller] = _blur_fbt  # add to cache

        # update size
        if cls._tmp_fbt.width != g.mWindowSize[0] or cls._tmp_fbt.height != g.mWindowSize[1]:
            cls._tmp_fbt.update_size(*g.mWindowSize)
        if _blur_fbt.width != _target_width or _blur_fbt.height != _target_height:
            _blur_fbt.update_size(_target_width, _target_height)

        # generate gui
        imgui.new_frame()
        with imgui.font(g.mFont):
            # Note: This Content should be same with GUI.render_ui()
            #    --> UIManager.u_render_ui()
            #        -->WindowManager.w_render()
            flags = imgui.WINDOW_NO_SAVED_SETTINGS | imgui.WINDOW_NO_INPUTS | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
            for window in ALL_WINDOWS:
                if window not in _exclude_windows:
                    window.w_show(flags=flags)
            # we do not render shadows here

        # render to temp frame buffer texture
        cls._tmp_fbt.fbo.use()
        cls._tmp_fbt.fbo.clear()
        imgui.render()
        g.mWindowEvent.imgui.render(imgui.get_draw_data())

        # calc blur
        _blur_fbt.render(
            texture=cls._tmp_fbt.texture,
            radius=user_settings.recommended_blur_radius
        )

        if callback:
            callback(_blur_fbt.texture)

        g.mIsHandlingBlurCommand = False

    @classmethod
    def _dummy(cls, *args, **kwargs):
        print("you are in dummy func")
