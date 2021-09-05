from core import Message
from dataSource import DataSource
from handlers.constraint import FuncInterface

from .calculator import Calculator
from .operator import Operator
from .material import Material
from .recruit import Recruit
from .enemy import Enemy
from .gacha import Gacha


class Arknights(DataSource):
    def __init__(self, bot):
        super().__init__(auto_update=True, check_assets=True)

        self.Calculator = Calculator(self)
        self.Operator = Operator(self, bot)
        self.Material = Material(self)
        self.Recruit = Recruit(self, bot)
        self.Enemy = Enemy(self)
        self.Gacha = Gacha(self)

        self.funcs = [
            self.Gacha,
            self.Calculator,
            self.Operator,
            self.Material,
            self.Recruit,
            self.Enemy,
        ]

    def find_results(self, data: Message):
        for item in self.funcs:
            item: FuncInterface

            if item.check(data):
                result = item.action(data)
                if result:
                    return result.rec(item.function_id)
