import random

from core import Message, Chain
from core.util.config import keyword
from core.util.common import word_in_sentence, check_sentence_by_re
from handlers.constraint import FuncInterface


@FuncInterface.is_disable_func(function_id='normal')
def emotion(data: Message):
    message = data.text

    reply = Chain(data)

    mood = data.user_info.user_mood

    name_good = keyword.name.good
    keyword_bad = keyword.keyword.bad
    keyword_good = keyword.keyword.good
    touch_reply = keyword.touch

    if check_sentence_by_re(message, keyword_bad, name_good):
        reply.feeling = -5

        if mood - 5 <= 0:
            return reply.text('(阿米娅没有应答...似乎已经生气了...)')

        anger = int((1 - (mood - 5) / 15) * 100)
        return reply.text(f'博士为什么要说这种话，阿米娅要生气了！[face67]（{anger}%）')

    if check_sentence_by_re(message, keyword_good, name_good):
        if mood < 0:
            if mood + 5 < 0:
                text = '哼！不要以为这样阿米娅就会轻易原谅博士...[face103]'
            else:
                text = '阿米娅这次就原谅博士吧，博士要好好对阿米娅哦[face21]'

            reply.feeling = 5
            return reply.text(text)
        else:
            if word_in_sentence(message, ['我错了', '对不起', '抱歉']):
                if mood >= 15:
                    return reply.text('博士为什么要这么说呢，嗯……博士是不是偷偷做了对不起阿米娅的事[face181]')
                else:
                    reply.feeling = 5
                    return reply.text('好吧，阿米娅就当博士刚刚是在开玩笑吧，博士要好好对阿米娅哦[face21]')

        reply.feeling = 5
        return reply.text(random.choice(touch_reply), trans_image=False)

    if mood < 0:
        return reply.text('哼~阿米娅生气了！不理博士！[face38]')
