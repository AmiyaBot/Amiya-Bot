from dataSource import DataSource
from handlers.functions.arknights.calculator import Calculator
from handlers.functions.arknights.operator import Operator
from handlers.functions.arknights.material import Material
from handlers.functions.arknights.recruit import Recruit
from handlers.functions.arknights.enemy import Enemy
from handlers.functions.arknights.gacha import Gacha


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
            self.Calculator,
            self.Operator,
            self.Material,
            self.Recruit,
            self.Enemy,
            self.Gacha,
        ]
