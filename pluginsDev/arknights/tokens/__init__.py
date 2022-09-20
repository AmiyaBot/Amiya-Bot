import os
import jieba

from amiyabot import PluginInstance

from core import log, Message, Chain, exec_before_init
from core.util import find_similar_list, extract_plugin
from core.resource.arknightsGameData import ArknightsGameData

curr_dir = os.path.dirname(__file__)
tokens_plugin = 'resource/plugins/tokens'

if curr_dir.endswith('.zip'):
    extract_plugin(curr_dir, tokens_plugin)
else:
    tokens_plugin = curr_dir

bot = PluginInstance(
    name='明日方舟关卡查询',
    version='1.0',
    plugin_id='amiyabot-arknights-tokens'
)


class InitToken:
    @staticmethod
    @exec_before_init
    async def init_token():
        log.info('building tokens keywords dict...')

        keywords = [f'{code} 500 n' for code in ArknightsGameData.tokens.keys()]

        with open(f'{tokens_plugin}/tokens.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(keywords))
        jieba.load_userdict(f'{tokens_plugin}/tokens.txt')


@bot.on_message(keywords=['召唤物'], allow_direct=True)
async def _(data: Message):
    text = data.text_origin.replace('召唤物', '', 1)
    result = find_similar_list(text, list(ArknightsGameData.tokens.keys()), _top_only=False)[0]

    if not result:
        return None

    tokens = []
    for r, l in result.items():
        if r < 1:
            continue
        tokens += [ArknightsGameData.tokens[item] for item in l]

    return Chain(data).html(f'{tokens_plugin}/template/token.html', {
        'tokens': [
            {
                'id': item.id,
                'type': item.type,
                'name': item.name,
                'en_name': item.en_name,
                'description': item.description,
                'attr': item.attr
            } for item in tokens
        ]
    })
