from database.baseController import BaseController
from modules.commonMethods import word_in_sentence

from functions.gacha.init import Init as Gacha
from functions.enemy.init import Init as Enemy
from functions.vblog.init import Init as VBlog
from functions.recruit.init import Init as Recruit
from functions.operator.init import Init as Operator
from functions.material.init import Init as Material
from functions.userInfo.init import Init as UserInfo
from functions.intellect.init import Init as Intellect
from functions.functionQuery.init import Init as FunctionQuery
from functions.jadeCalculator.init import Init as JadeCalculator

database = BaseController()


class FunctionsIndex:
    def __init__(self):
        priority = [
            FunctionQuery,
            JadeCalculator,
            Gacha,
            Enemy,
            Operator,
            Material,
            UserInfo,
            Recruit,
            Intellect,
            VBlog
        ]
        self.functions = [func() for func in priority]

    def action(self, data):
        for index, item in enumerate(self.functions):
            if word_in_sentence(data['text'], item.keyword):
                result = item.action(data)
                if result:
                    database.function.add_function_use_num(item.function_id)
                    return result
