import imgui

from gui.components import c
from gui.global_app_state import g
from gui.contents import DashBoard, CPU, GPU, Memory, PerformanceDebugger
from gui.windows.base_window import PopupWindow

# shapes
# https://thebookofshaders.com/edit.php?log=160414041142

class PerformanceInspectorWindow(PopupWindow):
    _name = 'PerformanceInspector'

    _curr_nav_idx = 0
    _contents = [DashBoard,
                 CPU,
                 GPU,
                 Memory,
                 PerformanceDebugger
                 ]
    _content_names_list = ['DashBoard',
                           'CPU',
                           'GPU',
                           'Memory',
                           'Performance Debugger'
                           ]
    _content_icons_list = ['dashboard',
                           'CPU',
                           'GPU',
                           'Random Access Memory',
                           'debug'
                           ]
    @classmethod
    def w_init(cls):
        super().w_init()

    @classmethod
    def w_update(cls):
        super().w_update()
        cls._contents[cls._curr_nav_idx].c_update()
    @classmethod
    def w_content(cls):
        # left part
        c.begin_child('performance inspector selector', width=imgui.get_window_width()/3, height=0, border=True)
        imgui.push_style_color(imgui.COLOR_BUTTON, 0, 0, 0, 0)
        imgui.push_style_var(imgui.STYLE_ITEM_SPACING, (g.mImguiStyle.item_spacing[0], g.mImguiStyle.item_spacing[1] * 2))
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, (g.mImguiStyle.frame_padding[0], g.mImguiStyle.frame_padding[1] * 2))
        for i in range(len(cls._contents)):
            if i == cls._curr_nav_idx:
                imgui.push_style_color(imgui.COLOR_BUTTON, *g.mImguiStyle.colors[imgui.COLOR_BUTTON_HOVERED])

            clicked = c.icon_text_button(cls._content_icons_list[i], cls._content_names_list[i],align_center=False, width=imgui.get_content_region_available_width())
            if i == cls._curr_nav_idx:
                imgui.pop_style_color(1)
            # clicked, state = imgui.menu_item(cls._content_names_list[i], None, cls._curr_nav_idx == i)
            if clicked:
                cls.switch_content(i)
        imgui.pop_style_color(1)
        imgui.pop_style_var(2)
        imgui.end_child()

        # right part
        imgui.same_line()
        c.begin_child('performance inspector content')
        cls._contents[cls._curr_nav_idx].c_show()
        imgui.end_child()

    @classmethod
    def w_open(cls):
        super().w_open()
        cls._contents[cls._curr_nav_idx].c_on_show()

    @classmethod
    def w_close(cls):
        super().w_close()
        cls._contents[cls._curr_nav_idx].c_on_hide()

    @classmethod
    def switch_content(cls, idx):
        if idx == cls._curr_nav_idx:
            return
        org_content = cls._contents[cls._curr_nav_idx]
        org_content.c_on_hide()
        new_content = cls._contents[idx]
        new_content.c_on_show()
        cls._curr_nav_idx = idx
