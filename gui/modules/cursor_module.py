import imgui
import pyglet

from gui.modules.base_module import BaseModule


class CursorModule(BaseModule):
    window = None

    @classmethod
    def m_init(cls):
        windows = pyglet.app.windows
        for window in windows:
            cls.window = window
            break
        assert cls.window is not None

    class CursorType:
        #: The default mouse cursor.
        CURSOR_DEFAULT = None
        #: A crosshair mouse cursor.
        CURSOR_CROSSHAIR = 'crosshair'
        #: A pointing hand mouse cursor.
        CURSOR_HAND = 'hand'
        #: A "help" mouse cursor; typically a question mark and an arrow.
        CURSOR_HELP = 'help'
        #: A mouse cursor indicating that the selected operation is not permitted.
        CURSOR_NO = 'no'
        #: A mouse cursor indicating the element can be resized.
        CURSOR_SIZE = 'size'
        #: A mouse cursor indicating the element can be resized from the top
        #: border.
        CURSOR_SIZE_UP = 'size_up'
        #: A mouse cursor indicating the element can be resized from the
        #: upper-right corner.
        CURSOR_SIZE_UP_RIGHT = 'size_up_right'
        #: A mouse cursor indicating the element can be resized from the right
        #: border.
        CURSOR_SIZE_RIGHT = 'size_right'
        #: A mouse cursor indicating the element can be resized from the lower-right
        #: corner.
        CURSOR_SIZE_DOWN_RIGHT = 'size_down_right'
        #: A mouse cursor indicating the element can be resized from the bottom
        #: border.
        CURSOR_SIZE_DOWN = 'size_down'
        #: A mouse cursor indicating the element can be resized from the lower-left
        #: corner.
        CURSOR_SIZE_DOWN_LEFT = 'size_down_left'
        #: A mouse cursor indicating the element can be resized from the left
        #: border.
        CURSOR_SIZE_LEFT = 'size_left'
        #: A mouse cursor indicating the element can be resized from the upper-left
        #: corner.
        CURSOR_SIZE_UP_LEFT = 'size_up_left'
        #: A mouse cursor indicating the element can be resized vertically.
        CURSOR_SIZE_UP_DOWN = 'size_up_down'
        #: A mouse cursor indicating the element can be resized horizontally.
        CURSOR_SIZE_LEFT_RIGHT = 'size_left_right'
        #: A text input mouse cursor (I-beam).
        CURSOR_TEXT = 'text'
        #: A "wait" mouse cursor; typically an hourglass or watch.
        CURSOR_WAIT = 'wait'
        #: The "wait" mouse cursor combined with an arrow.
        CURSOR_WAIT_ARROW = 'wait_arrow'

    CT = CursorType

    @classmethod
    def set_cursor(cls, cursor_type: 'CursorModule.CursorType'):
        cursor = CursorModule.window.get_system_mouse_cursor(cursor_type)
        CursorModule.window.set_mouse_cursor(cursor)

    @classmethod
    def set_default_cursor(cls):
        cls.set_cursor(CursorModule.CursorType.CURSOR_DEFAULT)

    class CursorRegion:
        def __init__(self, cursor_type: 'CursorModule.CursorType'):
            self.cursor_type = cursor_type
            self.in_region = False

        def update(self, region_min, region_max):
            """return tuple(changed, in_region)"""
            imgui_mouse_hovering_rect = imgui.is_mouse_hovering_rect(*region_min, *region_max, False)
            changed = False
            if imgui_mouse_hovering_rect and not self.in_region:
                # enter region
                self.in_region = True
                CursorModule.set_cursor(self.cursor_type)
                changed = True
            elif not imgui_mouse_hovering_rect and self.in_region:
                # exit region
                self.in_region = False
                CursorModule.set_cursor(CursorModule.CursorType.CURSOR_DEFAULT)
                changed = True
            return changed, self.in_region

    CR = CursorRegion
