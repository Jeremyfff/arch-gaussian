import logging

import imgui

from gui import components as c
from gui import global_var as g
from gui.modules import EventModule, LayoutModule, ShadowModule
from gui.windows.base_window import BaseWindow
from scripts.project_manager import ProjectManager


class NavBarWindow(BaseWindow):
    LAYOUT_NAME = 'level2_left'

    NAV_BUTTON_ICONS = ['stack-fill', 'rocket-2-fill', 'edit-box-fill']
    NAV_BUTTON_IDS = [f'nav_bar_icon_{i}' for i in range(len(NAV_BUTTON_ICONS))]
    NAV_TOOLTIPS = ['PREPARE DATASET', 'TRAIN 3DGS', 'EDIT 3DGS']
    assert len(NAV_TOOLTIPS) == len(NAV_BUTTON_ICONS)
    TRANSPARENT = (0, 0, 0, 0)

    @classmethod
    def w_init(cls):
        super().w_init()

    @classmethod
    def w_update(cls):
        super().w_update()
        if g.mCurrNavIdx == -1 and ProjectManager.curr_project is not None:
            cls.switch_nav_idx(0)

    @classmethod
    def w_show(cls):
        super().w_show()
        org_window_padding = g.mImguiStyle.window_padding
        org_frame_padding = g.mImguiStyle.frame_padding
        new_window_padding = (4, 10)
        frame_padding = org_frame_padding[0] + org_window_padding[0] - new_window_padding[0]
        new_frame_padding = (frame_padding, frame_padding)
        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, new_window_padding)
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, new_frame_padding)
        imgui.push_style_var(imgui.STYLE_ITEM_SPACING, (0, 10))
        with LayoutModule.LayoutWindow(cls.LAYOUT_NAME):
            BUTTON_COLOR = g.mImguiStyle.colors[imgui.COLOR_BUTTON]
            for i, icon in enumerate(cls.NAV_BUTTON_ICONS):
                if c.icon_button(icon, bg_color=BUTTON_COLOR if i == g.mCurrNavIdx else cls.TRANSPARENT,
                                 id=cls.NAV_BUTTON_IDS[i]):
                    cls.switch_nav_idx(i)
                c.easy_tooltip(cls.NAV_TOOLTIPS[i])
        imgui.pop_style_var(3)

    @classmethod
    def switch_nav_idx(cls, i):
        if g.mCurrNavIdx == i:
            return
        org_idx = g.mCurrNavIdx
        new_idx = i
        logging.info(f'[{cls.__name__}] nav idx changed from [{org_idx}] to [{new_idx}]')
        # event trigger
        EventModule.on_nav_idx_changed(org_idx, new_idx)
