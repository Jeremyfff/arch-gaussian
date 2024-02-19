import imgui

from gui import global_var as g
from gui import components as c
LAYOUT_NAME = 'level2_left'

NAV_BUTTON_ICONS = ['stack-fill', 'rocket-2-fill', 'edit-box-fill']
NAV_BUTTON_IDS = [f'nav_bar_icon_{i}' for i in range(len(NAV_BUTTON_ICONS))]
TRANSPARENT = (0, 0, 0, 0)
def show():
    imgui.set_next_window_size(*g.mLayoutScheme.get_size(LAYOUT_NAME))
    imgui.set_next_window_position(*g.mLayoutScheme.get_pos(LAYOUT_NAME))
    org_window_padding = g.mImguiStyle.window_padding
    org_frame_padding = g.mImguiStyle.frame_padding
    new_window_padding = (4, 10)
    frame_padding = org_frame_padding[0] + org_window_padding[0] - new_window_padding[0]
    new_frame_padding = (frame_padding, frame_padding)
    imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, new_window_padding)
    imgui.push_style_var(imgui.STYLE_FRAME_PADDING, new_frame_padding)
    imgui.push_style_var(imgui.STYLE_ITEM_SPACING, (0, 10))
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
    imgui.begin('nav_bar_window', flags=flags)
    # begin ===============================================
    BUTTON_COLOR = g.mImguiStyle.colors[imgui.COLOR_BUTTON]
    for i, icon in enumerate(NAV_BUTTON_ICONS):
        if c.icon_button(icon, bg_color=BUTTON_COLOR if i == g.mCurrNavIdx else TRANSPARENT, id=NAV_BUTTON_IDS[i]):
            print('switch to {}'.format(i))
            g.mCurrNavIdx = i

    # end =================================================
    imgui.end()
    imgui.pop_style_var(3)
