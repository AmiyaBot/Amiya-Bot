import os
import jieba

from typing import List
from core import log, bot, Message, Chain, exec_before_init
from core.util import read_yaml, any_match, find_similar_list
from core.resource.arknightsGameData import ArknightsGameData

setting = read_yaml('config/private/arknights.yaml').materialSetting
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

        for name in ArknightsGameData().materials_map.keys():
            MaterialData.materials.append(name)

        with open('resource/materials.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join([f'{name} 500 n' for name in MaterialData.materials]))

        jieba.load_userdict('resource/materials.txt')

    @classmethod
    def check_material(cls, name):
        game_data = ArknightsGameData()

        if name not in game_data.materials_map:
            return False

        material = game_data.materials[game_data.materials_map[name]]
        material_id = material['material_id']
        material_images = []

        text = f'博士，为你找到材料【{name}】的档案\n\n\n\n\n\n\n'
        icons = [
            {
                'path': material_images_source + material['material_icon'] + '.png',
                'size': 80,
                'pos': (side_padding, side_padding + line_height + int((line_height * 6 - 80) / 2))
            }
        ]

        if material_id in game_data.materials_made:
            made = game_data.materials_made[material_id]

            text += '可在【%s】通过以下配方%s：\n\n' % tuple(setting.made[made[0]['made_type']])
            for item in made:
                item_material = game_data.materials[item['use_material_id']]

                text += '%s%s * %s\n\n' % (' ' * 15, item_material['material_name'], item['use_number'])
                material_images.append(material_images_source + item_material['material_icon'] + '.png')

        if material_id in game_data.materials_source:
            source = game_data.materials_source[material_id]

            s_main = {
                'place': '主线关卡',
                'map': []
            }
            s_act = {
                'place': '活动',
                'map': []
            }

            for code in source.keys():
                if 'main' in code:
                    s_main['map'].append(code)
                else:
                    s_act['map'].append(code)

            for item in [s_main, s_act]:
                if item['map']:
                    text += '\n\n可在以下【%s】地图掉落：\n\n' % item['place']
                    for code in sorted(item['map']):
                        item = source[code]
                        stage = game_data.stages[code]
                        info = (stage['stage_name'], stage['stage_code'], setting.rate[item['source_rate']])

                        text += '【%s】%s %s\n' % info

        for index, item in enumerate(material_images):
            if os.path.exists(item):
                icons.append({
                    'path': item,
                    'size': icon_size,
                    'pos': (side_padding, line_height * 9 + index * line_height * 2)
                })

        text += '\n' + material['material_desc']

        return text, icons


async def verify(data: Message):
    res = any_match(data.text, ['材料'] + MaterialData.materials)

    return res


@bot.on_group_message(function_id='checkMaterial', verify=verify)
async def _(data: Message):
    words = sorted(
        jieba.lcut_for_search(data.text),
        reverse=True,
        key=lambda i: len(i)
    )

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
            return Chain(data).text_image(*result)
