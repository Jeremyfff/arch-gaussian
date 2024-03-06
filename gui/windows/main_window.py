import logging
import imgui
import gui.global_var as g
from gui.contents import PrepareContent, Train3DGSContent, Edit3DGSContent, \
    ViewerContent, NodeEditorContent, BlankContent, GUI_CONTENT_TYPES, VerticalResizeHandleContent
from gui.modules import EventModule, LayoutModule
from gui.windows.base_window import BaseWindow


class MainWindow(BaseWindow):
    LAYOUT_NAME = 'level2_right'
    page0_content: tuple[GUI_CONTENT_TYPES] = (PrepareContent, VerticalResizeHandleContent, NodeEditorContent)
    page1_content: tuple[GUI_CONTENT_TYPES] = (Train3DGSContent, VerticalResizeHandleContent, ViewerContent)
    page2_content: tuple[GUI_CONTENT_TYPES] = (Edit3DGSContent, VerticalResizeHandleContent, ViewerContent)
    pagen1_content: tuple[GUI_CONTENT_TYPES] = (BlankContent,)
    display_contents: dict[int:tuple[GUI_CONTENT_TYPES]] = {
        0: page0_content,
        1: page1_content,
        2: page2_content,
        -1: pagen1_content
    }

    first_loop = True

    curr_nav_idx = -1

    @classmethod
    def w_init(cls):
        super().w_init()
        # trigger is in nav_bar_window.py switch_nav_idx(idx)
        EventModule.register_nav_idx_change_callback(cls.on_nav_idx_changed)

    @classmethod
    def w_update(cls):
        super().w_update()

        if cls.first_loop:
            for content in cls.display_contents[cls.curr_nav_idx]:
                content.c_on_show()
            cls.first_loop = False
        cls.update_pages(cls.display_contents[cls.curr_nav_idx])

    @classmethod
    def w_show(cls):
        super().w_show()
        cls.show_pages(cls.display_contents[cls.curr_nav_idx])

    @classmethod
    def show_pages(cls, page_contents: tuple[GUI_CONTENT_TYPES]):
        if len(page_contents) == 1:
            cls.show_one_page(page_contents[0])
        elif len(page_contents) > 1:
            cls.show_multiple_pages(*page_contents)

    @classmethod
    def update_pages(cls, page_contents: tuple[GUI_CONTENT_TYPES]):
        for content in page_contents:
            content.c_update()

    @classmethod
    def show_one_page(cls, content: GUI_CONTENT_TYPES):
        with LayoutModule.LayoutWindow(cls.LAYOUT_NAME):
            content.c_show()

    @classmethod
    def show_multiple_pages(cls, *page_contents):
        if len(page_contents) == 2:
            # 没有resize handle
            with LayoutModule.LayoutWindow('level3_left'):
                page_contents[0].c_show()
            with LayoutModule.LayoutWindow('level3_right'):
                page_contents[1].c_show()
        elif len(page_contents) == 3:
            # 中间为resize handle

            imgui.push_style_var(imgui.STYLE_WINDOW_MIN_SIZE, (1, 1))
            imgui.push_style_var(imgui.STYLE_WINDOW_BORDERSIZE, 0)
            with LayoutModule.LayoutWindow('level3_middle'):
                page_contents[1].c_show()
            imgui.pop_style_var(2)
            with LayoutModule.LayoutWindow('level3_left'):
                page_contents[0].c_show()
            with LayoutModule.LayoutWindow('level3_right'):
                page_contents[2].c_show()

    @classmethod
    def on_nav_idx_changed(cls, org_idx: int, new_idx: int):
        logging.info(f'[{cls.__name__}] received nav idx changed event. (from [{org_idx}] to [{new_idx}])')

        org_contents = set(cls.display_contents[org_idx])
        new_contents = set(cls.display_contents[new_idx])

        org_contents_to_hide = org_contents - new_contents
        new_contents_to_show = new_contents - org_contents
        for content in org_contents_to_hide:
            try:
                content.c_on_hide()
            except Exception as e:
                print(e)
        for content in new_contents_to_show:
            try:
                content.c_on_show()
            except Exception as e:
                print(e)
        cls.curr_nav_idx = new_idx  # 本窗口的nav idx 由class的curr nav idx驱动， 而不由global var的mCurrNavIdx驱动
        g.mCurrNavIdx = new_idx
