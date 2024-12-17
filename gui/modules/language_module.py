import csv

from gui.modules.base_module import BaseModule
from gui.user_data import user_settings


class LanguageSet:

    def __init__(self):
        self._registered_translations: dict[str: list[str]] = {}  # dict{english_text: list[language_texts]}

    def register_translation(self, english: str, chinese: str = None):
        self._registered_translations[english] = [
            english,
            chinese
        ]

    def get_translation(self, english: str):
        try:
            return self._registered_translations[english][user_settings.language]
        except IndexError:
            # language translation not supported
            return f"[!error] language ({user_settings.language}) not supported"
        except KeyError:
            return f"[!error]\"{english}\" not registered"


class LanguageModule(BaseModule):
    @classmethod
    def m_init(cls):
        pass

    @classmethod
    def load_language_set(cls, file_path) -> LanguageSet:
        _l = LanguageSet()
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            csv_reader = csv.reader(file, delimiter=';')
            for row in csv_reader:
                if len(row) == 2:
                    _l.register_translation(english=row[0], chinese=row[1])
        return _l
