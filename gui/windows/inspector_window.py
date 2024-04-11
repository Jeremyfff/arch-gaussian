from typing import Callable, Optional

import imgui

from gui.windows.base_window import PopupWindow


class InspectorWindow(PopupWindow):
    _name = 'Inspector'

    content: Optional[Callable] = None
    args: tuple[any] = ()
    kwargs = {}
    results = ()
    # on_close_event: Optional[Callable] = None
    on_close_events: set[Callable] = set()

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
        for func in cls.on_close_events:
            func()

    @classmethod
    def w_content(cls):
        super().w_content()
        if cls.content is None:
            imgui.text('no content')
            return
        cls.results = cls.content(*cls.args, **cls.kwargs)

    @classmethod
    def register_content(cls, content, *args, **kwargs):
        cls.content = content
        cls.args = args
        cls.kwargs = kwargs
        if not cls.is_opened():
            cls.w_open()

    @classmethod
    def unregister_content(cls):
        cls.content = None

    @classmethod
    def register_w_close_event(cls, func):
        cls.on_close_events.add(func)

    @classmethod
    def get_results(cls):
        results = cls.results
        cls.results = ()
        return results


class GaussianInspectorWindow(InspectorWindow, PopupWindow):
    _name = "GaussianInspector"


class GeometryInspectorWindow(InspectorWindow, PopupWindow):
    _name = "GeometryInspectorWindow"
