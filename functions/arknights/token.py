import jieba

from core import log, bot, Message, Chain, exec_before_init
from core.util import find_similar_list
from core.resource.arknightsGameData import ArknightsGameData


class InitToken:
    @staticmethod
    @exec_before_init
    async def init_token():
        log.info('building tokens keywords dict...')

        keywords = [f'{code} 500 n' for code in ArknightsGameData.tokens.keys()]

        with open('resource/tokens.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(keywords))
        jieba.load_userdict('resource/tokens.txt')


@bot.on_message(keywords=['召唤物'], allow_direct=True)
async def _(data: Message):
    text = data.text_origin.replace('召唤物', '', 1)
    result = find_similar_list(text, ArknightsGameData.tokens.keys(), _top_only=False)[0]

    if not result:
        return None

    tokens = []
    for r, l in result.items():
        if r < 1:
            continue
        tokens += [ArknightsGameData.tokens[item] for item in l]

    return Chain(data).html('template/operator/operatorToken.html', {
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
