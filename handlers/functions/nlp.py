import random

from core import Message, Chain
from core.util.config import config
from core.util.baiduCloud import NaturalLanguage
from handlers.constraint import disable_func

nlp = NaturalLanguage(config('baiduCloud'))


@disable_func(function_id='normal')
def natural_language_processing(data: Message):
    result = nlp.emotion(data.text)
    if result and 'items' in result and result['items']:
        item = result['items'][0]
        label = item['label']
        text = ''

        if label == 'neutral':
            pass
        elif label == 'optimistic':
            text = '虽然听不懂博士在说什么，但阿米娅能感受到博士现在高兴的心情，欸嘿嘿……'
        elif label == 'pessimistic':
            text = '博士心情不好吗？阿米娅不懂怎么安慰博士，但阿米娅会默默陪在博士身边的'

        if 'replies' in item and item['replies']:
            text = random.choice(item['replies'])

        if text:
            return Chain(data).text(text)
