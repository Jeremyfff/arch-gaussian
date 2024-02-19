from typing import Optional
import imgui


# 仅仅储存与ui相关的内容


GUI_RESOURCES_ROOT = 'gui/resources/'
GLOBAL_SCALE = 1
FONT_SIZE = 16 * GLOBAL_SCALE

# [WINDOW EVENTS] (set in GUI.py)
mFirstLoop = True
mWindowEvent = None
mWindowSize = (0, 0)

# [FONTS] (set in GUI.py)
mFont = None
mFontBold = None
mNodeEditorFont = None
mNodeEditorFontBold = None

# init in style module
mImguiStyle: Optional[imgui.core.GuiStyle] = None
# init in layout module
mLayoutScheme = None
# nav bar
mCurrNavIdx = 0

