import abc

from functools import wraps
from core import Message, Chain
from core.util.config import func_setting
from core.database.models import Disable, Function


def check_global_state(function_id):
    setting = func_setting().globalState
    if hasattr(setting, function_id):
        if not getattr(setting, function_id):
            return False
    return True


def check_group_state(group_id, function_id):
    disable = Disable.select().where(
        Disable.group_id == group_id,
        Disable.function_id == function_id
    )
    if disable.count():
        return False
    return True


class FuncInterface:
    def __init__(self, function_id):
        self.function_id = function_id

    @staticmethod
    def priority(data: Message) -> bool:
        pass

    @abc.abstractmethod
    def check(self, data: Message) -> bool:
        pass

    @abc.abstractmethod
    def action(self, data: Message) -> Chain:
        pass

    @staticmethod
    def is_used(func):
        def check(cls, data: Message):
            result: Chain = func(cls, data)
            if result:
                Function \
                    .insert(function_id=cls.function_id) \
                    .on_conflict(conflict_target=[Function.function_id],
                                 update={Function.use_num: Function.use_num + 1}) \
                    .execute()
                return result

        return check

    @staticmethod
    def is_disable(func):
        def check(cls, data: Message):
            if not check_global_state(cls.function_id):
                return False
            if not check_group_state(data.group_id, cls.function_id):
                return False
            return func(cls, data)

        return check

    @staticmethod
    def is_disable_func(function_id):
        def decorator(func):
            @wraps(func)
            def action(*args, **kwargs):
                data: Message = args[0]
                if not check_global_state(function_id):
                    return False
                if not check_group_state(data.group_id, function_id):
                    return False
                return func(*args, **kwargs)

            return action

        return decorator
