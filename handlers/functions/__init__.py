from .user.intellectAlarm import IntellectAlarm
from .user.userInfo import UserInfo
from .menu.menu import Menu
from .weibo import Weibo
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
            UserInfo(),
            IntellectAlarm()
        ]
        self.actions = [
            emotion,
            natural_language_processing
        ]
