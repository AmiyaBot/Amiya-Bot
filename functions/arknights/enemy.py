import re
import jieba

from typing import List
from core import log, bot, Message, Chain, exec_before_init
from core.util import integer, any_match
from core.resource.arknightsGameData import ArknightsGameData

line_height = 16
side_padding = 10


def get_value(key, source):
    for item in key.split('.'):
        if item in source:
            source = source[item]
    return source['m_defined'], integer(source['m_value'])


class Enemy:
    enemies: List[str] = []

    @staticmethod
    @exec_before_init
    async def init_enemies():
        log.info('building enemies names keywords dict...')

        Enemy.enemies = list(ArknightsGameData().enemies.keys())

        with open('resource/enemies.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join([f'{name} 500 n' for name in Enemy.enemies]))

        jieba.load_userdict('resource/enemies.txt')

    @classmethod
    def find_enemies(cls, name: str):
        result = []
        for item in cls.enemies:
            if name == item:
                return [item]
            if name in item:
                result.append(item)

        return result

    @classmethod
    def get_enemy(cls, name: str):
        enemies = ArknightsGameData().enemies

        key_map = {
            'attributes.maxHp': {'title': 'maxHp', 'value': ''},
            'attributes.atk': {'title': 'atk', 'value': ''},
            'attributes.def': {'title': 'def', 'value': ''},
            'attributes.magicResistance': {'title': 'magicResistance', 'value': ''},
            'attributes.moveSpeed': {'title': 'moveSpeed', 'value': ''},
            'attributes.baseAttackTime': {'title': 'baseAttackTime', 'value': ''},
            'attributes.hpRecoveryPerSec': {'title': 'hpRecoveryPerSec', 'value': ''},
            'attributes.massLevel': {'title': 'massLevel', 'value': ''},
            'attributes.stunImmune': {'title': 'stunImmune', 'value': ''},
            'attributes.silenceImmune': {'title': 'silenceImmune', 'value': ''},
            'attributes.sleepImmune': {'title': 'sleepImmune', 'value': ''},
            'attributes.frozenImmune': {'title': 'frozenImmune', 'value': ''},
            'attributes.levitateImmune': {'title': 'levitateImmune', 'value': ''},
            'rangeRadius': {'title': 'rangeRadius', 'value': ''},
            'lifePointReduce': {'title': 'lifePointReduce', 'value': ''},
        }

        attrs = {}

        for item in enemies[name]['data']:
            attrs[item['level'] + 1] = {}

            detail_data = item['enemyData']
            for key in key_map:
                defined, value = get_value(key, detail_data)
                if defined:
                    key_map[key]['value'] = value
                else:
                    value = key_map[key]['value']

                attrs[item['level'] + 1][key_map[key]['title']] = value

        return {
            **enemies[name],
            'attrs': attrs
        }


async def verify(data: Message):
    name = any_match(data.text, Enemy.enemies)
    keyword = any_match(data.text, ['敌人', '敌方'])

    if name or keyword:
        return True, (3 if keyword else 1)
    return False


@bot.on_group_message(function_id='checkEnemy', verify=verify)
async def _(data: Message):
    message = data.text_origin
    words = data.text_cut

    for reg in ['敌人(.*)', '敌方(.*)', '(.*)敌人', '(.*)敌方']:
        r = re.search(re.compile(reg), message)
        if r:
            enemy_name = r.group(1)
            result = Enemy.find_enemies(enemy_name)
            if result:
                if len(result) == 1:
                    return Chain(data).html('enemy/enemy.html', Enemy.get_enemy(result[0]))

                text = '博士，为您搜索到以下敌方单位：\n\n'

                for index, item in enumerate(result):
                    text += f'[{index + 1}] {item}\n'

                text += '\n回复【序号】查询对应的敌方单位资料'

                wait = await data.waiting(Chain(data).text(text))
                if wait:
                    r = re.search(r'(\d+)', wait.text_digits)
                    if r:
                        index = abs(int(r.group(1))) - 1
                        if index >= len(result):
                            index = len(result) - 1

                        return Chain(data).html('enemy/enemy.html', Enemy.get_enemy(result[index]))
            else:
                return Chain(data).text('博士，没有找到敌方单位%s的资料呢 >.<' % enemy_name)

    for item in words:
        if item in Enemy.enemies:
            return Chain(data).html('enemy/enemy.html', Enemy.get_enemy(item))
