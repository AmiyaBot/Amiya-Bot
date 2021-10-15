from typing import List

from core import Message
from handlers.constraint import FuncInterface, sorted_candidate

from .user.intellectAlarm import IntellectAlarm
from .user.userInfo import UserInfo
from .menu.menu import Menu
from .weibo import Weibo
from .replace import Replace
from .arknights import Arknights

from .nlp import natural_language_processing
from .touch import random_reply
from .manager import manager_handler
from .user.emotion import emotion
from .user.greeting import greeting


class FunctionIndexes:
    def __init__(self, bot):
        self.arknights = Arknights(bot)
        self.functions = [
            Menu(),
            Weibo(),
            Replace(bot),
            UserInfo(),
            IntellectAlarm()
        ]
        self.actions = [
            emotion,
            natural_language_processing
        ]

    def find_functions_results(self, data: Message, extra_funcs: List[FuncInterface]):
        if extra_funcs is None:
            extra_funcs = []

        candidate = sorted_candidate(data, [*self.functions, *extra_funcs])

        for item in candidate:
            item: FuncInterface

            result = item.action(data)
            if result:
                return result.rec(item.function_id)
