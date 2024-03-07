import logging
from abc import abstractmethod


class BaseWindow:
    _inited= False

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
