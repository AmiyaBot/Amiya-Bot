import os
import json
import jieba
import asyncio

from amiyabot import PluginInstance
from amiyabot.network.httpRequests import http_requests

from core import log, Message, Chain, tasks_control
from core.util import any_match, find_similar_list, extract_zip_plugin
from core.resource import remote_config
from core.database.bot import *
from core.database.bot import db as bot_db
from core.resource.arknightsGameData import ArknightsGameData

curr_dir = os.path.dirname(__file__)
material_plugin = 'resource/plugins/material'

if curr_dir.endswith('.zip'):
    extract_zip_plugin(curr_dir, material_plugin)
else:
    material_plugin = curr_dir

material_images_source = 'resource/gamedata/item/'
icon_size = 34
line_height = 16
side_padding = 10


@table
class PenguinData(BotBaseModel):
    stageId: str = CharField(null=True)
    itemId: str = CharField(null=True)
    times: int = IntegerField(null=True)
    quantity: int = IntegerField(null=True)
    stdDev: float = FloatField(null=True)
    start: int = BigIntegerField(null=True)
    end: int = BigIntegerField(null=True)


class MaterialData:
    materials: List[str] = []

    @staticmethod
    async def save_penguin_data():
        async with log.catch('penguin data save error:'):
            res = await http_requests.get(remote_config.remote.penguin)
            res = json.loads(res)

            PenguinData.truncate_table()
            PenguinData.batch_insert(res['matrix'])

            log.info('penguin data save successful.')

    @staticmethod
    async def init_materials():
        log.info('building materials names keywords dict...')

        for name in ArknightsGameData.materials_map.keys():
            MaterialData.materials.append(name)

        with open(f'{material_plugin}/materials.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join([f'{name} 500 n' for name in MaterialData.materials]))

        jieba.load_userdict(f'{material_plugin}/materials.txt')

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
        penguin_data = bot_db.execute_sql(select_sql).fetchall()

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
                    'rate': source[code]['source_rate']
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


class MaterialPluginInstance(PluginInstance):
    def install(self):
        asyncio.create_task(MaterialData.save_penguin_data())
        asyncio.create_task(MaterialData.init_materials())


bot = MaterialPluginInstance(
    name='明日方舟材料物品查询',
    version='1.0',
    plugin_id='amiyabot-arknights-material',
    description='查询明日方舟材料和物品资料',
    document=f'{material_plugin}/README.md'
)


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
            return Chain(data).html(f'{material_plugin}/template/material.html', result)


@tasks_control.timed_task(each=3600)
async def _():
    await MaterialData.save_penguin_data()
