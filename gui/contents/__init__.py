from typing import Union

from gui.contents.blank_content import BlankContent
from gui.contents.edit_3dgs_content import Edit3DGSContent
from gui.contents.menu_content import MainMenuContent
from gui.contents.node_editor_content import NodeEditorContent
from gui.contents.prepare_content import PrepareContent
from gui.contents.resize_handle_content import VerticalResizeHandleContent
from gui.contents.settings_content import UserSettingsContent, ProjectSettingsContent, ImguiSettingsContent, StyleSettingsContent, AboutContent
from gui.contents.train_3dgs_content import Train3DGSContent
from gui.contents.viewer_content import ViewerContent
from gui.contents.hierarchy_content import HierarchyContent
from gui.contents.performance_inspector_content import DashBoard, CPU, GPU, Memory, PerformanceDebugger

GUI_CONTENT_TYPES = Union[
    BlankContent, Edit3DGSContent, NodeEditorContent,
    PrepareContent, Train3DGSContent, ViewerContent, VerticalResizeHandleContent,
    MainMenuContent,
    UserSettingsContent, ProjectSettingsContent, ImguiSettingsContent, StyleSettingsContent,AboutContent,
    HierarchyContent,
    DashBoard, CPU, GPU, Memory, PerformanceDebugger
]
