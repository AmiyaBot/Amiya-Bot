import os
import jieba
import asyncio

from amiyabot import PluginInstance

from core import log, Message, Chain
from core.util import any_match, remove_punctuation
from core.resource.arknightsGameData import ArknightsGameData

curr_dir = os.path.dirname(__file__)


class Stage:
    @staticmethod
    async def init_stages():
        log.info('building stages keywords dict...')

        stages = list(ArknightsGameData.stages_map.keys())

        with open(f'{curr_dir}/stages.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join([f'{name} 500 n' for name in stages]))

        jieba.load_userdict(f'{curr_dir}/stages.txt')


class StagePluginInstance(PluginInstance):
    def install(self):
        asyncio.create_task(Stage.init_stages())


bot = StagePluginInstance(
    name='明日方舟关卡查询',
    version='1.1',
    plugin_id='amiyabot-arknights-stages',
    plugin_type='official',
    description='查询明日方舟关卡资料',
    document=f'{curr_dir}/README.md'
)


@bot.on_message(keywords=['地图', '关卡'], allow_direct=True, level=5)
async def _(data: Message):
    words = jieba.lcut(
        remove_punctuation(data.text_initial, ['-']).upper().replace(' ', '')
    )

    level = ''
    level_str = ''
    if any_match(data.text, ['突袭']):
        level = '_hard'
        level_str = '（突袭）'
    if any_match(data.text, ['简单', '剧情']):
        level = '_easy'
        level_str = '（剧情）'
    if any_match(data.text, ['困难', '磨难']):
        level = '_tough'
        level_str = '（磨难）'

    stage_id = None
    stages_map = ArknightsGameData.stages_map

    for item in words:
        stage_key = item + level
        if stage_key in stages_map:
            stage_id = stages_map[stage_key]

    if stage_id:
        stage_data = ArknightsGameData.stages[stage_id]
        res = {
            **stage_data,
            'name': stage_data['name'] + level_str
        }
        return Chain(data).html(f'{curr_dir}/template/stage.html', res)
    else:
        return Chain(data).text('抱歉博士，没有查询到相关地图信息')
