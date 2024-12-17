import importlib

from gui.contents.pages.full_page import *
from gui.contents.pages.edit_3dgs_pages import *
from gui.contents.pages.prepare_pages import *
from gui.contents.pages.train_3dgs_pages import *
from gui.contents.pages.hierarchy_pages import *


def reload_pages():
    importlib.reload(full_page)
    importlib.reload(prepare_pages)
    importlib.reload(train_3dgs_pages)
    importlib.reload(edit_3dgs_pages)
    importlib.reload(hierarchy_pages)


def cache_data():
    return full_page.FullPage.__dict__


def restore_data(data: dict):
    for key, value in data.items():
        key: str = key
        if key.startswith("_") and not key.endswith("_") and hasattr(full_page.FullPage, key):
            setattr(full_page.FullPage, key, value)
            print(f"{key} has been restored")
