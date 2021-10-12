import abc

from typing import Union, List

from functools import wraps
from core import Message, Chain
from core.util.config import func_setting
from core.database.models import Disable, Function


class FuncInterface:
    def __init__(self, function_id):
        self.function_id = function_id

    @abc.abstractmethod
    def verify(self, data: Message) -> Union[int, float, bool]:
        """
        功能可行性校验，返回一个数值用于判断置信度，若直接返回布尔型，则会视作 0 或 1
        """
        return 0

    @abc.abstractmethod
    def action(self, data: Message) -> Chain:
        """
        功能的具体实现，返回 Chain 对象发送消息
        """
        pass

    def confidence(self):
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


def sorted_candidate(data: Message, funcs: List[FuncInterface]):
    candidate = {}

    for item in funcs:
        ratio = item.verify(data)
        if ratio:
            ratio = int(ratio) if type(ratio) is bool else ratio
            ratio = 0 if not ratio else ratio

            candidate[f'{ratio}-{item.function_id}'] = item

    sort = sorted(candidate.items(), key=lambda n: n[0], reverse=True)

    return [item[1] for item in sort]
