import logging
import os
from abc import abstractmethod

from gui.global_info import TRANSLATION_FOLDER
from gui.modules import LanguageModule
from gui.modules.language_module import LanguageSet


class BaseContent:
    _inited = False

    TRANSLATION_FILE_NAME: str = None  # 用户设置项

    _l: LanguageSet = None

    @classmethod
    @abstractmethod
    def c_init(cls):
        logging.info(f'[{cls.__name__}] init')

        if cls.TRANSLATION_FILE_NAME is None:
            logging.warning(f"There is no translation file for [{cls.__name__}]. To specify a translation file, go to [{TRANSLATION_FOLDER}] to add a translation csv file and specify the _translation_file_name property of the class.")
            cls._l = LanguageSet()  # we use an empty language set
        else:
            path = os.path.join(TRANSLATION_FOLDER, cls.TRANSLATION_FILE_NAME)
            try:
                cls._l = LanguageModule.load_language_set(path)
            except Exception as e:
                logging.error(f"[{cls.__name__}] Error loading language set at {path}. {e}")
                cls._l = LanguageSet()

        cls._inited = True

    @classmethod
    @abstractmethod
    def c_update(cls):
        """logical update (this is run under update context)"""
        if not cls._inited:
            cls.c_init()  # late init

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
