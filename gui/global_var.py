from typing import Optional

import imgui

# 仅仅储存与ui相关的内容


GUI_RESOURCES_ROOT = 'gui/resources/'
GLOBAL_SCALE = 1
FONT_SIZE = 16 * GLOBAL_SCALE

# [WINDOW EVENTS] (set in GUI.py)
mTime = 0
mFrametime = 1e-5
mFirstLoop = True
mWindowEvent: 'WindowEvents' = None
mWindowSize = (0, 0)

# [FONTS] (set in GUI.py)
mFont = None
mFontBold = None
mNodeEditorFont = None
mNodeEditorFontBold = None

# init in style module
mImguiStyle: Optional[imgui.core.GuiStyle] = None

# nav bar
mCurrNavIdx = -1

# shared texture
mSharedTexture = None  # 显示在texture viewer的texture

mLastFileDir = r'c://'
