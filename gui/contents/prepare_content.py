import imgui

from gui import global_var as g
from gui.contents import pages
from gui.contents.base_content import BaseContent
from gui.modules.animation_module import AnimatedPageGroup
from scripts import project_manager as pm


class PrepareContent(BaseContent):
    page_group = AnimatedPageGroup(vertical=True)

    @classmethod
    def c_init(cls):
        super().c_init()
        cls.page_group.add_page_obj(pages.PrepareMainPage)
        cls.page_group.add_page_obj(pages.PrepareExtractVideoPage)
        cls.page_group.add_page_obj(pages.PrepareGoogleEarthPage)
        cls.page_group.add_page_obj(pages.PrepareColmapPage)
        cls.page_group.add_page_obj(pages.PrepareLevel2Page)

    @classmethod
    def c_update(cls):
        super().c_update()
        pass

    @classmethod
    def c_show(cls):
        super().c_show()
        if pm.curr_project is None:
            imgui.text('Please Open A Project First')
            return
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING,
                             (g.mImguiStyle.frame_padding[0] * 1.5, g.mImguiStyle.frame_padding[1] * 1.5))
        imgui.push_style_var(imgui.STYLE_ITEM_SPACING,
                             (g.mImguiStyle.item_spacing[0] * 1.5, g.mImguiStyle.item_spacing[1] * 1.5))
        cls.page_group.show_level_guide()
        cls.page_group.show()
        imgui.pop_style_var(2)

    @classmethod
    def c_on_show(cls):
        super().c_on_show()
        pass

    @classmethod
    def c_on_hide(cls):
        super().c_on_hide()
        pass
