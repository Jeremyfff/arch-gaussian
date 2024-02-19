from gui import global_var as g
import imgui
from ImNodeEditor import NEStyle


def init():
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
    style.colors[imgui.COLOR_BUTTON_HOVERED] = (0.45, 0.45, 0.45, 1.00)
    style.colors[imgui.COLOR_BUTTON_ACTIVE] = (0.35, 0.35, 0.35, 1.00)
    style.colors[imgui.COLOR_HEADER] = (0.29, 0.29, 0.29, 1.00)
    style.colors[imgui.COLOR_HEADER_HOVERED] = (0.46, 0.46, 0.46, 1.00)
    style.colors[imgui.COLOR_HEADER_ACTIVE] = (0.44, 0.44, 0.44, 1.00)
    style.colors[imgui.COLOR_TAB] = (0.33, 0.33, 0.33, 1.00)
    style.colors[imgui.COLOR_TAB_HOVERED] = (0.46, 0.46, 0.46, 1.00)
    style.colors[imgui.COLOR_PLOT_HISTOGRAM] = (0.14, 0.50, 0.90, 1.00)
    style.colors[imgui.COLOR_MODAL_WINDOW_DIM_BACKGROUND] = (0.09, 0.09, 0.09, 0.89)

    style.window_rounding = 0
    style.child_rounding = 4
    style.frame_rounding = 4
    style.popup_rounding = 8


gray = (0.6, 0.6, 0.6, 1)
white = (1, 1, 1, 1)
black = (0, 0, 0, 0)
