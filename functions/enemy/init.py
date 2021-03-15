import re

from modules.commonMethods import Reply


class Init:
    def __init__(self):
        self.function_id = 'checkEnemy'
        self.keyword = ['敌人', '敌方']

    @staticmethod
    def action(data):
        return Reply('博士，敌人查询功能升级中，暂时无法使用哦')

    def __action(self, data):

        message = data['text']

        for item in ['敌人(.*)', '敌方(.*)']:
            r = re.search(re.compile(item), message)
            if r:
                enemy_name = r.group(1)
                result = self.find_enemy(enemy_name)
                if result:
                    return Reply(result)
                else:
                    return Reply('博士，没有找到%s的资料呢 >.<' % enemy_name)

    @staticmethod
    def find_enemy(enemy):
        return None
