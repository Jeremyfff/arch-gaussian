import logging
from abc import abstractmethod
from typing import Optional

from gui.modules.cell_module import CellModule

class BasePage:
    _inited = False
    parent_page_group = None
    page_name = ''
    page_level = -1
    page_pos_from = 200
    page_pos_to = 0
    cell_module:Optional[CellModule] = None

    @classmethod
    def set_parent_page_group(cls, parent):
        cls.parent_page_group = parent

    @classmethod
    def _p_init(cls):
        """在__call__之前自动调用"""
        assert cls.page_name != ''
        assert cls.page_level != -1
        logging.info(f'[{cls.__name__}] init')
        cls.p_init()
        cls._inited = True

    @classmethod
    def __call__(cls, ):
        if not cls._inited:
            cls._p_init()
        cls.p_call()

    @classmethod
    @abstractmethod
    def p_init(cls):
        """user def"""
        pass

    @classmethod
    @abstractmethod
    def p_call(cls):
        """user def"""
        pass
