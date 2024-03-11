import imgui

from gui import global_var as g
from gui.windows.base_window import PopupWindow


class TextureViewerWindow(PopupWindow):
    _name = 'TextureViewerWindow'

    @classmethod
    def w_init(cls):
        super().w_init()

    @classmethod
    def w_update(cls):
        super().w_update()

    @classmethod
    def w_open(cls):
        super().w_open()

    @classmethod
    def w_close(cls):
        super().w_close()

    @classmethod
    def w_content(cls):
        super().w_content()
        imgui.text('hello world')
        if g.mSharedTexture is None:
            return
        imgui.image(g.mSharedTexture.glo, g.mSharedTexture.width, g.mSharedTexture.height)
