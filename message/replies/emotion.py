import json
import random

from database.baseController import BaseController
from message.messageType import MessageType
from modules.commonMethods import Reply, word_in_sentence, check_sentence_by_re

database = BaseController()
MSG = MessageType()

with open('resource/words/keyword.json', encoding='utf-8') as file:
    keyword = json.load(file)
with open('resource/words/amiyaName.json', encoding='utf-8') as file:
    amiya_name = json.load(file)
with open('resource/words/talkWords.json', encoding='utf-8') as file:
    talk_words = json.load(file)


def emotion(data):
    message = data['text']
    user_id = data['user_id']
    nickname = data['nickname']

    mood = get_mood(user_id)

    if check_sentence_by_re(message, keyword['badWords'], amiya_name[0]):
        if mood < 0:
            return Reply('(阿米娅没有应答...)', -2, at=False)
        return Reply([
            MSG.text('检测到和Dr.%s的好感度正在下降，阿米娅准备生气了' % nickname),
            MSG.face(67)
        ], -5)

    if check_sentence_by_re(message, keyword['goodWords'], amiya_name[0]):
        if mood < 0:
            if mood + 5 < 0:
                text = [
                    MSG.text('哼！不要以为这样阿米娅就会轻易原谅博士'),
                    MSG.face(103)
                ]
            else:
                text = [
                    MSG.text('阿米娅这次就原谅博士吧，博士要好好对阿米娅哦'),
                    MSG.face(21)
                ]
            return Reply(text, 5)
        else:
            if word_in_sentence(message, ['我错了', '对不起']):
                return Reply('Dr.%s为什么要这么说呢，阿米娅没有生气哦' % nickname, 5)

        return Reply(random.choice(random.choice(talk_words)), 5, auto_image=False)

    if mood < 0:
        return Reply('哼~阿米娅生气了！不理博士！', 1)


def get_mood(user_id):
    mood = 0
    result = database.user.get_user(user_id)
    if result:
        mood = result[2]
    return mood
