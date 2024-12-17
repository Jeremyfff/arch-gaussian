import imgui

from gui.components import c
from gui.global_app_state import g

__runtime__ = True

from gui.modules import StyleModule

if not __runtime__:
    from gui.graphic import geometry


class GeometryUITemplate:
    def __init__(self, host: "geometry.BaseGeometry"):
        self.host = host

        self._imgui_name_variable = self.host.name
        self._imgui_editing_name = False

        self.editable_name = True
        self.show_active_button = True
        self.show_delete_self_button = True
        self.show_components = True
        self.show_material = True

    def operation_panel(self) -> tuple[bool, bool]:
        """提供了一个基础样板,
        return (changed, delete_self)

        =======================
        Name
        ------------------------
        [ ] Active [Delete Self]
        ------------------------
        Components
        ========================
        """
        changed = False
        delete_self = False

        imgui.push_id(self.host.uid)
        c.begin_child_auto_height(f"{self.host.name}_operation_panel")

        # region name
        imgui.push_id("name_region")
        if self.editable_name:
            changed |= self.op_template_editable_name()
        else:
            self.op_template_name()

        if self.show_active_button:
            changed |= self.op_template_active_button()
        if self.show_active_button and self.show_delete_self_button:
            imgui.same_line()
        if self.show_delete_self_button:
            delete_self |= self.op_template_delete_self_button()
        imgui.pop_id()
        # endregion

        # region Components

        if self.show_components:
            c.begin_child_auto_height(f"{self.host.name}_operation_panel_components_region", color=StyleModule.COLOR_GREEN)
            c.icon_image("component", width=g.font_size, height=g.font_size)
            imgui.same_line()
            c.bold_text("Components")
            for component in self.host.components:
                if imgui.tree_node(component.__class__.__name__, imgui.TREE_NODE_DEFAULT_OPEN):
                    component.operation_panel()
                    imgui.tree_pop()
            c.end_child_auto_height(f"{self.host.name}_operation_panel_components_region")
        # endregion

        # region material
        if self.show_material:
            c.begin_child_auto_height(f"{self.host.name}_operation_panel_material_region", color=StyleModule.COLOR_BLUE)
            c.icon_image("material", width=g.font_size, height=g.font_size)
            imgui.same_line()
            c.bold_text("Material")
            if self.host.material is not None:
                self.host.material.operation_panel()
            else:
                imgui.text("no material")
            c.end_child_auto_height(f"{self.host.name}_operation_panel_material_region")
        # endregion

        c.end_child_auto_height(f"{self.host.name}_operation_panel")
        imgui.pop_id()

        return changed, delete_self

    def op_template_editable_name(self) -> bool:
        """
        可编辑名字的标题栏
        """
        changed = False
        if self._imgui_editing_name:
            imgui.push_id(f'{self.host.name}_name_input')
            _, self._imgui_name_variable = imgui.input_text('', self._imgui_name_variable)
            imgui.pop_id()
            imgui.same_line()
            if imgui.button('confirm'):
                self.host.name = self._imgui_name_variable
                self._imgui_editing_name = False
                changed = True
            imgui.same_line()
            if imgui.button('cancel'):
                self._imgui_editing_name = False
        else:
            c.bold_text(self.host.name)
            if imgui.is_mouse_double_clicked(0) and imgui.is_item_hovered():
                self._imgui_editing_name = True
            c.easy_tooltip(f'Double click to rename')
        return changed

    def op_template_name(self) -> None:
        c.bold_text(self.host.name)

    def op_template_active_button(self) -> bool:
        changed, value = imgui.checkbox("Active", self.host.active)
        if changed:
            self.host.active = value
        return changed

    def op_template_delete_self_button(self) -> bool:
        _ = self
        return c.icon_text_button('delete-bin-fill', 'delete')
