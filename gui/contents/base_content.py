import logging
from abc import abstractmethod


class BaseContent:
    _inited = False

    @classmethod
    @abstractmethod
    def c_init(cls):
        logging.info(f'[{cls.__name__}] init')
        cls._inited = True

    @classmethod
    @abstractmethod
    def c_update(cls):
        """logical update (this is run under update context)"""
        pass

    @classmethod
    @abstractmethod
    def c_show(cls):
        if not cls._inited:
            cls.c_init()  # late init

    @classmethod
    @abstractmethod
    def c_on_show(cls):
        if not cls._inited:
            cls.c_init()  # late init
        logging.info(f'[{cls.__name__}] on_show')

    @classmethod
    @abstractmethod
    def c_on_hide(cls):
        logging.info(f'[{cls.__name__}] on_hide')
