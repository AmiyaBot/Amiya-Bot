import time

from core import Message, Chain
from core.util.config import reward
from core.database.models import User
from handlers.constraint import FuncInterface


@FuncInterface.is_disable_func(function_id='normal')
def greeting(data: Message):
    message = data.text
    nickname = data.nickname

    if data.is_bad_call:
        return Chain(data).text(f'哼！Dr.{nickname}不许叫人家{data.bad_name}，不然人家要生气了！')

    if '签到' in message and data.is_call:
        status = sign_in(data, 1)
        if status:
            return Chain(data).text(status['text'])

    if '晚安' in message:
        return Chain(data).text(f'Dr.{nickname}，晚安～')

    for item in ['早上好', '早安', '中午好', '午安', '下午好', '晚上好']:
        if item in message:
            hour = talk_time()
            text = ''
            if hour:
                text += f'Dr.{nickname}，{hour}好～'
            else:
                text += f'Dr.{nickname}，这么晚还不睡吗？要注意休息哦～'

            status = sign_in(data)
            if status['status']:
                text += status['text']

            return Chain(data).text(text)

    for item in ['不能休息', '不能停', '不要休息', '不要停', '很多事情']:
        if item in message:
            pass


def sign_in(data: Message, sign_type=0):
    user = data.user_info

    if user.sign_in == 0:
        coupon = reward.greeting.coupon
        feeling = reward.greeting.feeling
        User.update(
            sign_in=1,
            coupon=User.coupon + coupon,
            user_feeling=User.user_feeling + feeling,
            sign_times=User.sign_times + 1
        ).where(User.user_id == data.user_id).execute()
        return {
            'text': f'{"签到成功，" if sign_type else ""}{coupon}张寻访凭证已经送到博士的办公室啦，请博士注意查收哦',
            'status': True
        }

    if sign_type and user.sign_in == 1:
        return {
            'text': '博士今天已经签到了哦',
            'status': False
        }

    return {'status': False}


def talk_time():
    localtime = time.localtime(time.time())
    hours = localtime.tm_hour
    if 0 <= hours <= 5:
        return ''
    elif 5 < hours <= 11:
        return '早上'
    elif 11 < hours <= 14:
        return '中午'
    elif 14 < hours <= 18:
        return '下午'
    elif 18 < hours <= 24:
        return '晚上'
