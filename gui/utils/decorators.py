from typing import Callable

from gui.common import register_update_func, register_start_func, register_update_ui_func


def my_decorator(func):
    def wrapper():
        print("Before calling the function")
        func()
        print("After calling the function")

    return wrapper


def start_func(func: Callable):
    register_start_func(func.__name__, func)
    return func


def update_func(func: Callable):
    register_update_func(func.__name__, func)
    return func


def update_ui_func(func: Callable):
    register_update_ui_func(func.__name__, func)
