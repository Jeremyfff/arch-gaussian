from typing import Optional

import imgui

from gui.user_data import user_settings  # user data and user setting can be imported here

# 共享的app状态信息，实时更新
# 程序关闭后，这些信息不会被保存

__runtime__ = True
if not __runtime__:
    # for type hint
    from GUI import WindowEvents
    from gui.components import Components
    from gui.modules.graphic_module import FrameBufferTexture, BlurFBT
    from gui.windows import WindowManager

    raise Exception("This code will never be reached")


class GlobalAppState:
    def __init__(self):
        # [WINDOW EVENTS] (set in GUI.py)
        self.mTime = 0
        self.mFrametime = 1e-5
        self.mFirstLoop = True
        self.mWindowEvent: Optional['WindowEvents'] = None
        self.mWindowSize: tuple[int, int] = (0, 0)

        self.mIsClosing = False
        self.mConfirmClose = False

        # [FONTS] (set in GUI.py)
        self.mFont = None
        self.mFontBold = None
        self.mFontLarge = None
        self.mNodeEditorFont = None
        self.mNodeEditorFontBold = None

        # init in style module
        self.mImguiStyle: Optional[imgui.core.GuiStyle] = None

        # nav bar
        self.mCurrNavIdx = -1

        # shared texture
        self.mSharedTexture = None  # 显示在texture viewer的texture

        # io utils
        self.mLastFileDir = r'c://'

        # viewer content
        self.mImagePos = (0, 0)

        self.mShiftDown = False
        self.mCtrlDown = False

        # Settings
        self.mIsUserSettingsContentOpen = False  # 是否正在打开userSettings面板， 很多地方会检测该值来判断是否需要实时更新某些参数

        # misc
        self._mCachedComponentsModule: Optional["Components"] = None

        self.mWindowManager: Optional["WindowManager"] = None

        self.mIsHandlingBlurCommand = False  # 是否正在执行模糊的重新渲染操作，在渲染时使用该标签以节约性能，并且避免fbo.use问题， 在没有进行模糊渲染时，可以在imgui 的ui render中使用fbo.use()方法
    @property
    def global_scale(self):
        return user_settings.global_scale

    @property
    def font_size(self):
        return 16 * self.global_scale

    @property
    def c(self) -> "Components":
        """
        这里也提供了一个通过g获取c的方法，采用lazy load的方法
        :return:
        """
        # lazy load
        if self._mCachedComponentsModule is None:
            from gui import components
            self._mCachedComponentsModule = components
        return self._mCachedComponentsModule


g = GlobalAppState()
