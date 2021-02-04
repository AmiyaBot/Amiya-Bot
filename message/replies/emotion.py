import json
import random

from database.baseController import BaseController
from modules.commonMethods import Reply, word_in_sentence, check_sentence_by_re

database = BaseController()

with open('resource/words/keyword.json', encoding='utf-8') as file:
    keyword = json.load(file)
with open('resource/words/amiyaName.json', encoding='utf-8') as file:
    amiya_name = json.load(file)
with open('resource/words/talkWords.json', encoding='utf-8') as file:
    talk_words = json.load(file)


def emotion(data):
    message = data['text']
    user_id = data['user_id']

    mood = get_mood(user_id)

    if check_sentence_by_re(message, keyword['badWords'], amiya_name[0]):
        if mood - 5 <= 0:
            return Reply('(阿米娅没有应答...似乎已经生气了...)', -5, at=False)

        anger = int((1 - (mood - 5) / 15) * 100)

        return Reply('博士为什么要说这种话，阿米娅要生气了！[face67]（{anger}%）'.format(anger=anger), -5)

    if check_sentence_by_re(message, keyword['goodWords'], amiya_name[0]):
        if mood < 0:
            if mood + 5 < 0:
                text = '哼！不要以为这样阿米娅就会轻易原谅博士...[face103]'
            else:
                text = '阿米娅这次就原谅博士吧，博士要好好对阿米娅哦[face21]'
            return Reply(text, 5)
        else:
            if word_in_sentence(message, ['我错了', '对不起', '抱歉']):
                if mood >= 15:
                    return Reply('博士为什么要这么说呢，嗯……博士是不是偷偷做了对不起阿米娅的事[face181]', 5)
                else:
                    return Reply('好吧，阿米娅就当博士刚刚是在开玩笑吧，博士要好好对阿米娅哦[face21]', 5)

        return Reply(random.choice(random.choice(talk_words)), 5, auto_image=False)

    if mood < 0:
        return Reply('哼~阿米娅生气了！不理博士！[face38]', 1)


def get_mood(user_id):
    mood = 15
    result = database.user.get_user(user_id)
    if result:
        mood = result['user_mood']
    else:
        database.user.update_user(user_id, 0)
    return mood
