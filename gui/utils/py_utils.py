import inspect


def get_caller_class():
    caller_frame = inspect.currentframe().f_back.f_back
    caller_class = caller_frame.f_locals.get('cls', None)
    return caller_class
