from abc import abstractmethod

import logging
class BaseContent:
    _inited_contents = set()

    @classmethod
    @abstractmethod
    def c_init(cls):
        logging.info(f'[{cls.__name__}] init')
        BaseContent._inited_contents.add(cls)

    @classmethod
    @abstractmethod
    def c_update(cls):
        """logical update (this is run under update context)"""
        pass

    @classmethod
    @abstractmethod
    def c_show(cls):
        if cls not in BaseContent._inited_contents:
            cls.c_init()  # late init

    @classmethod
    @abstractmethod
    def c_on_show(cls):
        if cls not in BaseContent._inited_contents:
            cls.c_init()  # late init
        logging.info(f'[{cls.__name__}] on_show')

    @classmethod
    @abstractmethod
    def c_on_hide(cls):
        logging.info(f'[{cls.__name__}] on_hide')
