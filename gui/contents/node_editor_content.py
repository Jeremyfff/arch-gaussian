import imgui
from ImNodeEditor import NE, Node

from gui.global_app_state import g
from gui.contents.base_content import BaseContent
from gui.modules import my_node_module


class NodeEditorContent(BaseContent):
    @classmethod
    def c_init(cls):
        super().c_init()
        pass

    @classmethod
    def c_update(cls):
        super().c_update()
        Node.main_loop()

    @classmethod
    def c_show(cls):
        super().c_show()
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

    @classmethod
    def c_on_show(cls):
        super().c_on_show()
        pass

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()
        pass
