import imgui
from ImNodeEditor import NE, Node
from gui import global_var as g
from gui.modules import my_node_module


def show():
    if imgui.button('save'): Node.save('./node_file.bin')
    imgui.same_line()
    if imgui.button('load'): Node.load('./node_file.bin')
    imgui.same_line()
    if imgui.button('edit pin colors'): imgui.open_popup('pin color editor')
    if imgui.begin_popup('pin color editor'):
        my_node_module.show_pin_color_editor()
        if imgui.button('copy code'): my_node_module.copy_pin_colors()
        imgui.end_popup()
    imgui.same_line()
    if imgui.button('edit node colors'): imgui.open_popup('node color editor')
    if imgui.begin_popup('node color editor'):
        my_node_module.show_node_color_editor()
        if imgui.button('copy code'): my_node_module.copy_node_colors()
        imgui.end_popup()
    imgui.same_line()
    imgui.text(f'{(1 / NE.FRAME_TIME):.0f} fps')
    with imgui.font(g.mNodeEditorFont):
        imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, 0, 0, 0, 0)
        NE.begin()  # NE :: begin node editor canvas
        Node.draw_all_nodes()  # Node :: draw all nodes
        NE.end()  # NE :: end node editor canvas
        imgui.pop_style_color()
