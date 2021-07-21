import random

from library.baiduCloud import NaturalLanguage
from modules.config import get_config
from modules.commonMethods import Reply

config = get_config('baidu_cloud')
nlp = NaturalLanguage(config)


def natural_language_processing(data):
    result = None
    try:
        result = nlp.emotion(data['text'])
    except Exception as e:
        print('NLP', e)

    if result:
        item = result['items'][0]
        text = ''

        if 'replies' in item and item['replies']:
            text = random.choice(item['replies'])

        label = item['label']
        if label == 'neutral':
            pass
        elif label == 'optimistic':
            text = '虽然听不懂博士在说什么，但阿米娅能感受到博士现在高兴的心情，欸嘿嘿……'
        elif label == 'pessimistic':
            text = '博士心情不好吗？阿米娅不懂怎么安慰博士，但阿米娅会默默陪在博士身边的'

        if text:
            return Reply(text)
