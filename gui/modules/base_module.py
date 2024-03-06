import logging
from abc import abstractmethod


class BaseModule:
    @classmethod
    @abstractmethod
    def m_init(cls):
        logging.info(f'[{cls.__name__}] init')
