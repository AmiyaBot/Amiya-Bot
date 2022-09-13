import jieba

from core import log, bot, Message, Chain, exec_before_init
from core.util import any_match, remove_punctuation
from core.resource.arknightsGameData import ArknightsGameData


class Stage:
    @staticmethod
    @exec_before_init
    async def init_enemies():
        log.info('building stages keywords dict...')

        stages = list(ArknightsGameData.stages_map.keys())

        with open('resource/stages.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join([f'{name} 500 n' for name in stages]))

        jieba.load_userdict('resource/stages.txt')


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
        return Chain(data).html('template/stage/stage.html', res)
    else:
        return Chain(data).text('抱歉博士，没有查询到相关地图信息')
