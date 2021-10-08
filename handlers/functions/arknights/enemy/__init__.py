import re
import jieba

from core import Message, Chain
from core.util import log
from core.util.common import find_similar_list, remove_xml_tag, integer
from core.util.imageCreator import line_height, side_padding
from dataSource import DataSource
from handlers.constraint import FuncInterface


class Enemy(FuncInterface):
    def __init__(self, data_source: DataSource):
        super().__init__(function_id='checkEnemy')

        self.data = data_source
        self.keywords = list(data_source.enemies.keys())

        self.init_enemies()

        jieba.load_userdict('resource/enemies.txt')

    def init_enemies(self):
        log.info('building enemies\'s names keywords dict...')
        with open('resource/enemies.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join([f'{name} 500 n' for name in self.keywords]))

    @staticmethod
    def priority(data: Message):
        for item in ['敌人', '敌方']:
            if item in data.text:
                return True
        return False

    @FuncInterface.is_disable
    def check(self, data: Message):
        for item in ['敌人', '敌方'] + self.keywords:
            if item in data.text:
                return True
        return False

    @FuncInterface.is_used
    def action(self, data: Message):

        message = data.text
        words = data.text_cut
        reply = Chain(data)

        for item in words:
            if item in self.keywords:
                return reply.text_image(*self.find_enemy(item))

        for reg in ['敌人(.*)', '敌方(.*)', '(.*)敌人', '(.*)敌方']:
            r = re.search(re.compile(reg), message)
            if r:
                enemy_name = r.group(1)
                name, rate = find_similar_list(enemy_name, self.keywords, _random=True)
                if name:
                    return reply.text_image(*self.find_enemy(name))
                else:
                    return reply.text('博士，没有找到敌人%s的资料呢 >.<' % enemy_name)

    def find_enemy(self, name):
        data = self.data.enemies[name]['info']
        detail = self.data.enemies[name]['data']

        text = '博士，为您找到了敌方档案\n\n\n\n\n\n\n'
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
                    text += '    - [%s]\n    -- 初动 %ss，冷却 %ss\n' % sk_info

        icons = [
            {
                'path': 'resource/images/enemy/%s.png' % data['enemyId'],
                'size': 80,
                'pos': (side_padding, side_padding + line_height + int((line_height * 6 - 80) / 2))
            }
        ]

        return text, icons

    @staticmethod
    def get_value(key, source):
        for item in key.split('.'):
            if item in source:
                source = source[item]
        return source['m_defined'], integer(source['m_value'])
