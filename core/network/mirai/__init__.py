import collections
from functools import wraps


def func_with_name(name):
    def _(func):
        def _(*args, **kwargs):
            command_func_name_dict[func] = name
            return func(*args, **kwargs)
        return _
    return _


def get_func_name(name: str):
    return command_func_name_dict.get(name)


command_func_name_dict = collections.defaultdict(str)
