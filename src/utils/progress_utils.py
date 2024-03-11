import inspect
from typing import Optional, Callable

_update_func: Optional[Callable] = None
_total = 100
_ctx_name = ''
_update_func_ctx_name = ''
_curr = 0


def create_contex(ctx_name, func):
    global _update_func, _update_func_ctx_name, _curr
    _update_func = func
    _update_func_ctx_name = ctx_name
    _curr = 0



def get_total():
    return _total


def new_progress(total):
    global _total, _ctx_name
    caller = inspect.stack()[1].function
    _total = total
    _ctx_name = caller


def update(n=1):
    global _curr
    _curr += n
    if _update_func is not None and _ctx_name == _update_func_ctx_name:
        _update_func(_curr)
