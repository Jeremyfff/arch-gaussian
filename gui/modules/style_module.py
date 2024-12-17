import imgui

from gui.global_app_state import g
from gui.modules.base_module import BaseModule
from gui.utils import color_utils


class StyleModule(BaseModule):
    COLOR_GRAY = (0.6, 0.6, 0.6, 1)
    COLOR_DARK_GRAY = (0.3, 0.3, 0.3, 1)
    COLOR_WHITE = (1, 1, 1, 1)
    COLOR_BLACK = (0, 0, 0, 1)
    COLOR_BLUE = (0.2, 0.41, 0.68, 1)
    COLOR_GREEN = (0.1, 0.6, 0.3, 1)
    COLOR_YELLOW = (0.9, 0.7, 0.1, 1)
    COLOR_RED = (0.8, 0.2, 0.2, 1)

    COLOR_PRIMARY = COLOR_BLUE
    COLOR_SECONDARY = COLOR_GRAY
    COLOR_SUCCESS = COLOR_GREEN
    COLOR_WARNING = COLOR_YELLOW
    COLOR_DANGER = COLOR_RED
    COLOR_DISABLED = COLOR_DARK_GRAY

    COLOR_PRIMARY_LIGHTENED = color_utils.lighten_color(COLOR_PRIMARY, 0.1)

    @classmethod
    def m_init(cls):
        super().m_init()

        from gui.modules import EventModule
        EventModule.register_global_scale_change_callback(cls._on_global_scale_changed)

        style: imgui.core.GuiStyle = imgui.get_style()
        g.mImguiStyle = style

        style.colors[imgui.COLOR_TEXT] = (1.00, 1.00, 1.00, 1.00)
        style.colors[imgui.COLOR_WINDOW_BACKGROUND] = (0.12, 0.12, 0.12, 1.00)
        style.colors[imgui.COLOR_BORDER] = (0.20, 0.20, 0.20, 0.50)
        style.colors[imgui.COLOR_FRAME_BACKGROUND] = (0.32, 0.32, 0.32, 0.54)
        style.colors[imgui.COLOR_FRAME_BACKGROUND_HOVERED] = (0.73, 0.73, 0.73, 0.40)

        style.colors[imgui.COLOR_FRAME_BACKGROUND_ACTIVE] = (0.98, 0.98, 0.98, 0.67)
        style.colors[imgui.COLOR_TITLE_BACKGROUND] = (0.25, 0.25, 0.25, 1.00)
        style.colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = (0.23, 0.37, 0.58, 1.00)
        style.colors[imgui.COLOR_BUTTON] = (0.35, 0.35, 0.35, 1.00)
        style.colors[imgui.COLOR_BUTTON_HOVERED] = (0.40, 0.40, 0.40, 1.00)
        style.colors[imgui.COLOR_BUTTON_ACTIVE] = (0.35, 0.35, 0.35, 1.00)
        style.colors[imgui.COLOR_HEADER] = (0.29, 0.29, 0.29, 1.00)
        style.colors[imgui.COLOR_HEADER_HOVERED] = (0.46, 0.46, 0.46, 1.00)
        style.colors[imgui.COLOR_HEADER_ACTIVE] = (0.44, 0.44, 0.44, 1.00)
        style.colors[imgui.COLOR_TAB] = (0.33, 0.33, 0.33, 1.00)
        style.colors[imgui.COLOR_TAB_HOVERED] = (0.46, 0.46, 0.46, 1.00)
        style.colors[imgui.COLOR_PLOT_HISTOGRAM] = (0.14, 0.50, 0.90, 1.00)
        style.colors[imgui.COLOR_MODAL_WINDOW_DIM_BACKGROUND] = (0.09, 0.09, 0.09, 0.89)

        style.window_rounding = 4
        style.child_rounding = 4 * g.global_scale
        style.frame_rounding = 4 * g.global_scale
        style.popup_rounding = 8 * g.global_scale
        style.tab_rounding = 4 * g.global_scale
        style.scrollbar_rounding = 9 * g.global_scale
        style.grab_rounding = 0 * g.global_scale

        style.window_padding = (8 * g.global_scale, 8 * g.global_scale)
        style.frame_padding = (4 * g.global_scale, 3 * g.global_scale)
        style.cell_padding = (4 * g.global_scale, 2 * g.global_scale)

        style.item_spacing = (8 * g.global_scale, 4 * g.global_scale)
        style.indent_spacing = 21 * g.global_scale
        style.item_inner_spacing = (4 * g.global_scale, 4 * g.global_scale)

    @classmethod
    def push_highlighted_button_color(cls):
        color = color_utils.align_alpha(cls.COLOR_PRIMARY, g.mImguiStyle.colors[imgui.COLOR_BUTTON])
        lighten_color = color_utils.align_alpha(cls.COLOR_PRIMARY_LIGHTENED, g.mImguiStyle.colors[imgui.COLOR_BUTTON])

        imgui.push_style_color(imgui.COLOR_BUTTON, *color)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *lighten_color)
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, *color)

    @classmethod
    def pop_button_color(cls):
        imgui.pop_style_color(3)

    @classmethod
    def push_disabled_button_color(cls):
        color = color_utils.align_alpha(cls.COLOR_DISABLED, g.mImguiStyle.colors[imgui.COLOR_BUTTON])
        imgui.push_style_color(imgui.COLOR_BUTTON, *color)
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, *color)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *color)

    @classmethod
    def _on_global_scale_changed(cls):
        cls.m_init()
