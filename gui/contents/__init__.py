from typing import Union

from gui.contents.blank_content import BlankContent
from gui.contents.edit_3dgs_content import Edit3DGSContent
from gui.contents.node_editor_content import NodeEditorContent
from gui.contents.prepare_content import PrepareContent
from gui.contents.train_3dgs_content import Train3DGSContent
from gui.contents.viewer_content import ViewerContent
from gui.contents.resize_handle_content import VerticalResizeHandleContent

GUI_CONTENT_TYPES = Union[
    BlankContent, Edit3DGSContent, NodeEditorContent,
    PrepareContent, Train3DGSContent, ViewerContent, VerticalResizeHandleContent
]
