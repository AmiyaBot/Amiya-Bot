import re

from modules.commonMethods import Reply, find_similar_string, remove_xml_tag
from message.messageType import TextImage
from modules.dataSource.gameData import GameData


class Init:
    def __init__(self):
        self.function_id = 'checkEnemy'
        self.keyword = ['敌人', '敌方']
        self.enemies = GameData().init_enemies()

    def action(self, data):

        message = data['text']

        for reg in ['敌人(.*)', '敌方(.*)']:
            r = re.search(re.compile(reg), message)
            if r:
                enemy_name = r.group(1)
                result = self.find_enemy(enemy_name)
                if result:
                    return Reply(result)
                else:
                    return Reply('博士，没有找到%s的资料呢 >.<' % enemy_name)

    def find_enemy(self, enemy):
        name = find_similar_string(enemy, list(self.enemies.keys()))
        if name:
            try:
                data = self.enemies[name]['info']
                detail = self.enemies[name]['data']

                text = '博士，这是找到的敌方档案\n\n\n\n\n\n\n'
                text += '【%s】\n\n' % name
                text += '%s\n\n' % data['description']
                text += '[能力]\n%s\n\n' % remove_xml_tag(data['ability'] or '无')
                text += '[属性]\n耐久 %s | 攻击力 %s | 防御力 %s | 法术抗性 %s\n' % \
                        (data['endure'],
                         data['attack'],
                         data['defence'],
                         data['resistance'])

                key_map = {
                    'attributes.maxHp': {'title': '生命值', 'value': ''},
                    'attributes.atk': {'title': '攻击力', 'value': ''},
                    'attributes.def': {'title': '物理防御', 'value': ''},
                    'attributes.magicResistance': {'title': '魔法抗性', 'value': ''},
                    'attributes.moveSpeed': {'title': '移动速度', 'value': ''},
                    'attributes.baseAttackTime': {'title': '攻击间隔', 'value': ''},
                    'attributes.hpRecoveryPerSec': {'title': '生命回复/秒', 'value': ''},
                    'attributes.massLevel': {'title': '重量', 'value': ''},
                    'rangeRadius': {'title': '攻击距离/格', 'value': ''},
                    'lifePointReduce': {'title': '进点损失', 'value': ''}
                }

                for item in detail:
                    text += '\n[等级 %s 数值]\n' % (item['level'] + 1)
                    detail_data = item['enemyData']
                    key_index = 0
                    for key in key_map:
                        defined, value = self.get_value(key, detail_data)
                        if defined:
                            key_map[key]['value'] = value
                        else:
                            value = key_map[key]['value']

                        text += '%s：%s%s' % (key_map[key]['title'], value, '    ' if key_index % 2 == 0 else '\n')
                        key_index += 1
                    if detail_data['skills']:
                        text += '技能冷却时间：\n'
                        for sk in detail_data['skills']:
                            sk_info = (sk['prefabKey'], sk['initCooldown'], sk['cooldown'])
                            text += '    - [%s]\n    -- 初始冷却 %ss，后续冷却 %ss\n' % sk_info

                icons = [
                    {
                        'path': 'resource/images/enemy/%s.png' % data['enemyId'],
                        'size': (80, 80),
                        'pos': (10, 30)
                    }
                ]

                return TextImage(text, icons)
            except Exception as e:
                raise e
                print('Enemy', e)
                return '博士，【%s】档案好像损坏了... >.<' % name
        else:
            return False

    @staticmethod
    def get_value(key, source):
        for item in key.split('.'):
            if item in source:
                source = source[item]
        return source['m_defined'], source['m_value']
