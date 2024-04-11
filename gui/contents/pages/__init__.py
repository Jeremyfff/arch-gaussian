import importlib

from gui.contents.pages.full_page import *
from gui.contents.pages.edit_3dgs_pages import *
from gui.contents.pages.prepare_pages import *
from gui.contents.pages.train_3dgs_pages import *


def reload_pages():
    importlib.reload(full_page)
    importlib.reload(prepare_pages)
    importlib.reload(train_3dgs_pages)
    importlib.reload(edit_3dgs_pages)
