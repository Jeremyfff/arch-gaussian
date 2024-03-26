import logging
from abc import abstractmethod

import imgui


class BaseWindow:
    _inited = False

    @classmethod
    @abstractmethod
    def w_init(cls):
        logging.info(f'[{cls.__name__}] init')
        cls._inited = True

    @classmethod
    @abstractmethod
    def w_update(cls):
        if not cls._inited:
            cls.w_init()  # late init

    @classmethod
    @abstractmethod
    def w_show(cls):
        if not cls._inited:
            cls.w_init()  # late init


class PopupWindow(BaseWindow):
    _opened = False
    _active = False
    _position = (0, 0)
    _size = (0, 0)
    _name = ''

    @classmethod
    @abstractmethod
    def w_init(cls):
        super().w_init()
        cls._name = cls.__name__ if cls._name == '' else cls._name

    @classmethod
    @abstractmethod
    def w_update(cls):
        super().w_update()

    @classmethod
    def w_show(cls):
        """no need to implement"""
        if not cls._opened:
            return
        super().w_show()
        expanded, opened = imgui.begin(cls._name, True)
        cls._position = imgui.get_window_position()
        cls._size = imgui.get_window_size()
        cls._active = imgui.is_window_focused()
        cls.w_content()
        imgui.end()
        if not opened:
            cls.w_close()

    @classmethod
    @abstractmethod
    def w_open(cls):
        cls._opened = True

    @classmethod
    @abstractmethod
    def w_close(cls):
        cls._opened = False

    @classmethod
    @abstractmethod
    def w_content(cls):
        pass

    @classmethod
    def is_opened(cls):
        return cls._opened

    @classmethod
    def is_active(cls):
        return cls._active

    @classmethod
    def get_rect_min(cls):
        return cls._position

    @classmethod
    def get_rect_max(cls):
        return cls._position[0] + cls._size[0], cls._position[1] + cls._size[1]
