import abc

from functools import wraps
from core import Message, Chain
from core.database.models import Disable, Function


def disable_func(function_id):
    def decorator(func):
        @wraps(func)
        def action(*args, **kwargs):
            data: Message = args[0]
            disable = Disable.select().where(
                Disable.group_id == data.group_id,
                Disable.function_id == function_id
            )
            if disable.count():
                return False
            return func(*args, **kwargs)

        return action

    return decorator


class FuncId:
    function_id = None


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
    def is_disable(func):
        def check(cls: FuncId, data: Message):
            disable = Disable.select().where(
                Disable.group_id == data.group_id,
                Disable.function_id == cls.function_id
            )
            if disable.count():
                return False
            return func(cls, data)

        return check

    @staticmethod
    def is_used(func):
        def check(cls: FuncId, data: Message):
            result: Chain = func(cls, data)
            if result:
                Function \
                    .insert(function_id=cls.function_id) \
                    .on_conflict(conflict_target=[Function.function_id],
                                 update={Function.use_num: Function.use_num + 1}) \
                    .execute()
                return result

        return check
