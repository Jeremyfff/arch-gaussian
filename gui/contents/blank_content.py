import logging
import os
import random

import imgui

from gui.components import c
from gui.contents.base_content import BaseContent
from gui.global_app_state import g
from gui.global_info import *
from gui.graphic import shader_toy_library as shader_lib
from gui.modules import StyleModule, DrawingModule, EventModule
from gui.modules.animation_module import Tween, Ease
from gui.modules.graphic_module import ShaderToyFBT, BlurFBT
from gui.user_data import user_settings
from gui.utils import io_utils
from scripts.project_manager import ProjectManager

welcome_text = """ Introducing the all-new EchoSphere Smart Speaker – your gateway to a seamless smart home experience.
Experience the power of voice control with EchoSphere, your personal assistant that responds to your every command. 
From playing your favorite music to setting reminders and controlling smart devices, 
EchoSphere is designed to make your life easier and more convenient.
With its sleek and modern design, EchoSphere seamlessly blends into any room decor, adding a touch of sophistication to 
your living space. Its advanced sound technology ensures crystal-clear audio for an immersive listening experience.
"""


class BlankContent(BaseContent):
    TRANSLATION_FILE_NAME = os.path.basename(__file__).replace(".py", ".csv")

    _fbt: ShaderToyFBT = None
    _blur_fbt: BlurFBT = None
    _scroll_percent = 0.0

    @classmethod
    def c_init(cls):
        super().c_init()
        cls._init_fbt()
        cls._blur_fbt = BlurFBT("planar_light_tunnel_blur", 600, 400)

    @classmethod
    def c_update(cls):
        super().c_update()

        cls._fbt.render()
        ky = 2.0 / (cls._scroll_percent + 1.0)  # 随着滚动变柔和
        bgc = g.mImguiStyle.colors[imgui.COLOR_WINDOW_BACKGROUND][:3]
        cls._blur_fbt.render(texture=cls._fbt.texture,
                             radius=user_settings.recommended_blur_radius * 4,
                             ky=ky,
                             by=ky * (2 * cls._scroll_percent - 1 + 0.65),  # 提前65%,
                             tint0=(*bgc, 0.01),
                             tint1=(*bgc, 0.4)
                             )

    @classmethod
    def c_show(cls):
        super().c_show()
        window_pos = imgui.get_window_position()
        window_width = int(imgui.get_window_width())
        window_height = int(imgui.get_window_height())
        cls._fbt.update_size(window_width, window_height)
        cls._blur_fbt.update_size(window_width, window_height)
        cls._scroll_percent = min(imgui.get_scroll_y() / window_height / 2.0, 1.0)  # 除以 2.0 让其滚动的慢一些
        DrawingModule.draw_image(cls._blur_fbt.texture_id, window_pos[0], window_pos[1], window_width + window_pos[0], window_height + window_pos[1], draw_list_type="window")

        imgui.dummy(window_width, window_height * 0.6)
        with imgui.font(g.mFontLarge):
            c.text("Arch Gaussian", center=True)
        imgui.dummy(window_width, imgui.get_frame_height())
        c.gray_text("Photorealistic Three-Dimensional City Generation with 3D Gaussian Splatting and Deep Learning", center=True)
        c.gray_text("Jeremy Feng", center=True)
        c.gray_text("Inst. AAA, School of Architecture, Southeast University", center=True)
        imgui.dummy(window_width, imgui.get_frame_height())
        imgui.push_style_var(imgui.STYLE_FRAME_ROUNDING, 50 * g.global_scale)
        # Get Started 按钮
        if c.button(cls._l.get_translation("Get Started"), 175 * g.global_scale, 40 * g.global_scale, True, True, None):
            Tween.start_animation("auto_scroll", imgui.get_scroll_y(), window_height, 1.25, function=cls._set_scroll_y, ease=Ease.QuadraticInOut)
        Tween.step_animation("auto_scroll")

        imgui.pop_style_var()
        content_width = 600 * g.global_scale
        content_height = 300 * g.global_scale
        dummy_height = (window_height - content_height) / 2
        imgui.dummy(window_width, dummy_height + window_height * 0.1)

        start_x = (window_width - content_width) / 2
        imgui.set_cursor_pos_x(start_x)
        imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, 0, 0, 0, 0)
        # begin child
        c.begin_child('welcome', content_width, content_height, border=False)
        flags = imgui.WINDOW_NO_SCROLLBAR
        inner_width = content_width / 2 - g.mImguiStyle.window_padding[0] - g.mImguiStyle.item_spacing[0] / 2
        inner_height = content_height - 2 * g.mImguiStyle.window_padding[1]
        c.begin_child('left', inner_width - 20 * g.global_scale, inner_height, border=False, flags=flags)
        # left part content
        cls._left_part_content()
        imgui.end_child()

        imgui.same_line()
        imgui.set_cursor_pos_x(imgui.get_cursor_pos_x() + 20 * g.global_scale)
        c.begin_child('right', inner_width, inner_height, border=False, flags=flags)
        # right part content
        cls._right_part_content()

        imgui.end_child()
        # end child
        imgui.end_child()
        imgui.pop_style_color()

        imgui.dummy(width=window_width, height=dummy_height)

        imgui.set_cursor_pos((window_width - 100 * g.global_scale, window_height - 100 * g.global_scale + imgui.get_scroll_y()))
        if c.icon_button("shift-line", 32 * g.global_scale, 32 * g.global_scale, tooltip=cls._l.get_translation("Back to Top")):
            Tween.start_animation("auto_scroll_to_top", imgui.get_scroll_y(), 0, 1.0, cls._set_scroll_y, ease=Ease.QuadraticInOut)
        Tween.step_animation("auto_scroll_to_top")

    @classmethod
    def c_on_show(cls):
        super().c_on_show()
        EventModule.register_mouse_scroll_callback(cls._on_user_scroll)
        EventModule.register_mouse_press_callback(cls._on_user_press)
        EventModule.register_bg_style_change_callback(cls._on_bg_style_change)

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()
        EventModule.unregister_mouse_scroll_callback(cls._on_user_scroll)
        EventModule.unregister_mouse_press_callback(cls._on_user_press)
        EventModule.unregister_bg_style_change_callback(cls._on_bg_style_change)

    @classmethod
    def _left_part_content(cls):
        imgui.push_style_color(imgui.COLOR_TEXT, *StyleModule.COLOR_GRAY)
        imgui.text_wrapped(welcome_text)
        imgui.pop_style_color()

    @classmethod
    def _right_part_content(cls):
        _confirm_create_project_path = ''
        _confirm_create_project = False

        imgui.push_style_var(imgui.STYLE_ITEM_SPACING, (4, 10 * g.global_scale))
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING,
                             (g.mImguiStyle.frame_padding[0] * 2, g.mImguiStyle.window_padding[1] * 2))

        with imgui.font(g.mFontBold):
            imgui.text('ARCH GAUSSIAN V0.1')
        imgui.text('')
        imgui.text('')
        imgui.text('')
        if c.icon_text_button('folder-add-line', 'New Project...', imgui.get_content_region_available_width()):
            folder_path = io_utils.open_folder_dialog()
            if folder_path:
                ProjectManager.create_project(os.path.basename(folder_path), folder_path)
        if c.icon_text_button('folder-open-line', 'Open Project...', imgui.get_content_region_available_width()):
            folder_path = io_utils.open_folder_dialog()
            if folder_path:
                project = ProjectManager.open_folder_as_project(folder_path)
                if project is None:  # project not created yet
                    _confirm_create_project_path = folder_path
                    _confirm_create_project = True
        imgui.separator()
        c.icon_text_button('git-repository-line', 'Open Repository...', imgui.get_content_region_available_width())
        imgui.pop_style_var(2)

        # create project confirm popup
        c.create_project_confirm_popup(_confirm_create_project, _confirm_create_project_path)

    @classmethod
    def _init_fbt(cls):
        if cls._fbt is not None:
            del cls._fbt

        bg_style = user_settings.bg_style
        if bg_style < -1 or bg_style >= NUM_BG_STYLES:
            logging.error(f"bg_style({user_settings.bg_style}) in user settings exceed the max NUM_BG_STYLES({NUM_BG_STYLES}), the bg_style reset to default -1")
            bg_style = -1
            user_settings.bg_style = -1
        if bg_style == -1:
            bg_style = random.randint(0, NUM_BG_STYLES - 1)
        # a = 3
        if bg_style == 0:
            cls._fbt = shader_lib.Gradient_OneShader()
        elif bg_style == 1:
            cls._fbt = shader_lib.Tunnel_OneShader()
        elif bg_style == 2:
            cls._fbt = shader_lib.Podcast_OneShader()
        elif bg_style == 3:
            cls._fbt = shader_lib.Facebook_Connect_OneShader()
        else:
            cls._fbt = shader_lib.AtmosphericScatteringSkyBox_ShaderToy()

    @classmethod
    def _set_scroll_y(cls, y):
        imgui.set_scroll_y(y)

    @classmethod
    def _on_user_scroll(cls, x, y):
        Tween.stop_animation("auto_scroll")
        Tween.stop_animation("auto_scroll_to_top")

    @classmethod
    def _on_user_press(cls, x, y, b):
        Tween.stop_animation("auto_scroll")
        Tween.step_animation("auto_scroll_to_top")

    @classmethod
    def _on_bg_style_change(cls):
        cls._init_fbt()
