from typing import Dict, Type

from core import Message
from dataSource import DataSource
from handlers.constraint import FuncInterface
from handlers.functions.arknights.calculator import Calculator
from handlers.functions.arknights.operator import Operator
from handlers.functions.arknights.material import Material
from handlers.functions.arknights.recruit import Recruit
from handlers.functions.arknights.enemy import Enemy
from handlers.functions.arknights.gacha import Gacha

function_dict: Dict[str, Type[FuncInterface]] = {
    'jadeCalculator': Calculator,
    'checkOperator': Operator,
    'checkMaterial': Material,
    'checkEnemy': Enemy,
    'recruit': Recruit,
    'gacha': Gacha
}


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
            self.Enemy,
            self.Recruit,
        ]

    def find_results(self, data: Message):
        for item in self.funcs:
            item: FuncInterface

            if item.check(data):
                result = item.action(data)
                if result:
                    return result.rec(item.function_id)
