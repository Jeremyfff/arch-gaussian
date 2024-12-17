import logging

import imgui

from gui.components import c
from gui.global_app_state import g
from gui.modules import EventModule, LayoutModule
from gui.windows.base_window import BaseWindow
from scripts.project_manager import ProjectManager, ProjectDataKeys


class NavBarWindow(BaseWindow):
    LAYOUT_NAME = 'level2_left'

    NAV_BUTTON_ICONS = ['stack-fill', 'rocket-2-fill', 'edit-box-fill', 'stack-fill']
    NAV_BUTTON_IDS = [f'nav_bar_icon_{i}' for i in range(len(NAV_BUTTON_ICONS))]
    NAV_TOOLTIPS = ['PREPARE DATASET', 'TRAIN 3DGS', 'EDIT 3DGS', 'HIERARCHY']

    SEPARATE_IDXES = {3}  # 在这些Index的Icon之前加入分隔符
    assert len(NAV_TOOLTIPS) == len(NAV_BUTTON_ICONS)
    TRANSPARENT = (0, 0, 0, 0)

    @classmethod
    def w_init(cls):
        super().w_init()

    @classmethod
    def w_update(cls):
        super().w_update()

    @classmethod
    def w_show(cls, **kwargs):
        super().w_show()
        org_window_padding = g.mImguiStyle.window_padding
        org_frame_padding = g.mImguiStyle.frame_padding
        new_window_padding = (4 * g.global_scale, 10 * g.global_scale)
        frame_padding = org_frame_padding[0] + org_window_padding[0] - new_window_padding[0]
        new_frame_padding = (frame_padding, frame_padding)
        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, new_window_padding)
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, new_frame_padding)
        imgui.push_style_var(imgui.STYLE_ITEM_SPACING, (0, 10 * g.global_scale))
        with LayoutModule.LayoutWindow(cls.LAYOUT_NAME):
            BUTTON_COLOR = g.mImguiStyle.colors[imgui.COLOR_BUTTON]
            for i, icon in enumerate(cls.NAV_BUTTON_ICONS):
                if i in cls.SEPARATE_IDXES:
                    imgui.dummy(0, 5 * g.global_scale)
                    imgui.separator()
                    imgui.dummy(0, 5 * g.global_scale)
                if c.icon_button(icon, bg_color=BUTTON_COLOR if i == g.mCurrNavIdx else cls.TRANSPARENT,
                                 id=cls.NAV_BUTTON_IDS[i]):
                    cls.switch_nav_idx(i)
                c.easy_tooltip(cls.NAV_TOOLTIPS[i])

            # home button
            if c.icon_button("home", bg_color=cls.TRANSPARENT, id=-1):
                cls.switch_nav_idx(-1)

        imgui.pop_style_var(3)

    @classmethod
    def switch_nav_idx(cls, i):
        if g.mCurrNavIdx == i:
            logging.warning(f"[{cls.__name__}] nav idx [{i}] is the same as g.mCurrNavIdx, skip")
            return

        org_idx = g.mCurrNavIdx
        new_idx = i
        g.mCurrNavIdx = new_idx
        logging.info(f'[{cls.__name__}] nav idx changed from [{org_idx}] to [{new_idx}]')
        # event trigger
        EventModule.on_nav_idx_changed(org_idx, new_idx)
        # project data
        if ProjectManager.curr_project is not None:
            ProjectManager.curr_project.set_project_data(ProjectDataKeys.LAST_NAV_IDX, i)

    @classmethod
    def on_project_change(cls):
        if ProjectManager.curr_project is None:
            cls.switch_nav_idx(-1)
            return
        cls.switch_nav_idx(ProjectManager.curr_project.get_project_data(ProjectDataKeys.LAST_NAV_IDX, 0))


EventModule.register_project_change_callback(NavBarWindow.on_project_change)
