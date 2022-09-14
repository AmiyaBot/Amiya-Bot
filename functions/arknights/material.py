import jieba

from typing import List

from core import log, bot, Message, Chain, exec_before_init
from core.util import read_yaml, any_match, find_similar_list
from core.database.bot import db
from core.resource.arknightsGameData import ArknightsGameData

setting = read_yaml('config/arknights.yaml').materialSetting
material_images_source = 'resource/gamedata/item/'
icon_size = 34
line_height = 16
side_padding = 10


class MaterialData:
    materials: List[str] = []

    @staticmethod
    @exec_before_init
    async def init_materials():
        log.info('building materials names keywords dict...')

        for name in ArknightsGameData.materials_map.keys():
            MaterialData.materials.append(name)

        with open('resource/materials.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join([f'{name} 500 n' for name in MaterialData.materials]))

        jieba.load_userdict('resource/materials.txt')

    @classmethod
    def find_material_children(cls, material_id):
        game_data = ArknightsGameData
        children = []

        if material_id in game_data.materials_made:
            for item in game_data.materials_made[material_id]:
                children.append({
                    **item,
                    **game_data.materials[item['use_material_id']],
                    'children': cls.find_material_children(item['use_material_id'])
                })

        return children

    @classmethod
    def check_material(cls, name):
        game_data = ArknightsGameData

        if name not in game_data.materials_map:
            return None

        material = game_data.materials[game_data.materials_map[name]]
        material_id = material['material_id']

        select_sql = f'SELECT stageId, (quantity * 1.0) / (times * 1.0) AS rate ' \
                     f'FROM penguin_data WHERE itemId = "{material_id}" ORDER BY rate DESC LIMIT 10'
        penguin_data = db.execute_sql(select_sql).fetchall()

        result = {
            'name': name,
            'info': material,
            'children': cls.find_material_children(material_id),
            'source': {
                'main': [],
                'act': []
            },
            'recommend': []
        }

        if material_id in game_data.materials_source:
            source = game_data.materials_source[material_id]

            for code in source.keys():
                stage = game_data.stages[code]
                info = {
                    'code': stage['code'],
                    'name': stage['name'],
                    'rate': setting.rate[source[code]['source_rate']]
                }

                if 'main' in code:
                    result['source']['main'].append(info)
                else:
                    result['source']['act'].append(info)

        if penguin_data:
            recommend = []
            for item in penguin_data:
                stage_id = item[0].rstrip('_perm')
                rate = float(item[1])

                if stage_id not in game_data.stages:
                    continue

                stage = game_data.stages[stage_id]

                recommend.append({
                    'stageId': stage_id,
                    'stageType': stage['stageType'],
                    'apCost': stage['apCost'],
                    'code': stage['code'],
                    'name': stage['name'] + ('（磨难）' if 'tough' in stage_id else ''),
                    'rate': rate,
                    'desired': (stage['apCost'] / rate) if rate else 0
                })

            result['recommend'] = sorted(recommend, key=lambda n: n['desired'])

        return result


async def verify(data: Message):
    res = any_match(data.text, ['材料'] + MaterialData.materials)

    return res, 2


@bot.on_message(verify=verify, allow_direct=True)
async def _(data: Message):
    words = sorted(
        jieba.lcut_for_search(data.text),
        reverse=True,
        key=lambda i: len(i)
    )

    if '材料' in words:
        words.remove('材料')

    if not words:
        wait = await data.wait(Chain(data).text('博士，请说明需要查询的材料名称'))
        if not wait or not wait.text:
            return None
        words.append(wait.text)

    name = ''
    rate = 0
    for item in words:
        n, r = find_similar_list(item, MaterialData.materials, _random=True)
        if rate < r:
            name = n
            rate = r

    if name:
        result = MaterialData.check_material(name)
        if result:
            return Chain(data).html('template/material/material.html', result)
