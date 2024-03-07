import importlib


from gui.contents.pages.prepare_pages import *
from gui.contents.pages.train_3dgs_pages import *


def reload_pages():
    importlib.reload(prepare_pages)
    importlib.reload(train_3dgs_pages)

