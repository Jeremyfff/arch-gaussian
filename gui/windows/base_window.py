import logging
from abc import abstractmethod


class BaseWindow:
    _inited_windows = set()

    @classmethod
    @abstractmethod
    def w_init(cls):
        logging.info(f'[{cls.__name__}] init')
        BaseWindow._inited_windows.add(cls)

    @classmethod
    @abstractmethod
    def w_update(cls):
        pass

    @classmethod
    @abstractmethod
    def w_show(cls):
        pass
