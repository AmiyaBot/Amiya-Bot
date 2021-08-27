from core import Message
from dataSource import GameData

from ..funcInterface import FuncInterface

from .calculator import Calculator
from .operator import Operator
from .material import Material
from .recruit import Recruit
from .enemy import Enemy
from .gacha import Gacha


class Arknights(GameData):
    def __init__(self, bot):
        super().__init__(auto_update=True, check_assets=True)

        self.funcs = [
            Calculator(self),
            Operator(self),
            Material(self),
            Recruit(self, bot),
            Enemy(self),
            Gacha(self),
        ]

    def find_results(self, data: Message):
        for item in self.funcs:
            item: FuncInterface

            if item.check(data):
                result = item.action(data)
                if result:
                    return result.rec(item.function_id)
