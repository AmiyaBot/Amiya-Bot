import os
import jieba
import asyncio

from amiyabot import PluginInstance

from core import log, Message, Chain
from core.util import find_similar_list, extract_zip_plugin
from core.resource.arknightsGameData import ArknightsGameData

curr_dir = os.path.dirname(__file__)
tokens_plugin = 'resource/plugins/tokens'

if curr_dir.endswith('.zip'):
    extract_zip_plugin(curr_dir, tokens_plugin)
else:
    tokens_plugin = curr_dir


class InitToken:
    @staticmethod
    async def init_token():
        log.info('building tokens keywords dict...')

        keywords = [f'{code} 500 n' for code in ArknightsGameData.tokens.keys()]

        with open(f'{tokens_plugin}/tokens.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(keywords))
        jieba.load_userdict(f'{tokens_plugin}/tokens.txt')


class TokenPluginInstance(PluginInstance):
    def install(self):
        asyncio.create_task(InitToken.init_token())


bot = TokenPluginInstance(
    name='明日方舟召唤物查询',
    version='1.0',
    plugin_id='amiyabot-arknights-tokens',
    description='查询明日方舟召唤物资料',
    document=f'{tokens_plugin}/README.md'
)


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
