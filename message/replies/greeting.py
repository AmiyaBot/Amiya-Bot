import json
import time

from database.baseController import BaseController
from modules.commonMethods import Reply, word_in_sentence

database = BaseController()

with open('resource/words/amiyaName.json', encoding='utf-8') as file:
    amiya_name = json.load(file)

reward = 50


def greeting(data):
    message = data['text']
    nickname = data['nickname']

    for item in ['不能休息', '不能停', '不要休息', '不要停', '很多事情']:
        if item in message:
            pass

    for item in ['早上好', '早安', '中午好', '午安', '下午好', '晚上好']:
        if item in message:
            hour = talk_time()
            text = ''
            if hour:
                text += 'Dr.%s，%s好～' % (nickname, hour)
            else:
                text += 'Dr.%s，这么晚还不睡吗？要注意休息哦～' % nickname
            status = sign_in(data)

            if status['status']:
                text += '\n' + status['text']

            feeling = reward if status['status'] else 2
            coupon = reward if status['status'] else 0
            sign = 1 if status['status'] else 0

            return Reply(text, feeling, sign=sign, coupon=coupon)

    if '签到' in message and word_in_sentence(message, amiya_name[0]):
        status = sign_in(data, 1)
        if status:
            feeling = reward if status['status'] else 2
            coupon = reward if status['status'] else 0
            sign = 1 if status['status'] else 0

            return Reply(status['text'], feeling, sign=sign, coupon=coupon)

    if '晚安' in message:
        return Reply('Dr.%s，晚安～' % nickname)

    for name in amiya_name[1]:
        if message.find(name) == 0:
            return Reply('哼！Dr.%s不许叫人家%s，不然人家要生气了！' % (nickname, name), -3)


def sign_in(data, sign_type=0):
    user_id = data['user_id']
    user = database.user.get_user(user_id)

    if bool(user) is False or user['sign_in'] == 0:
        return {
            'text': '签到成功，%d张寻访凭证已经送到博士的办公室啦，请博士注意查收哦' % reward,
            'status': True
        }

    if sign_type and user['sign_in'] == 1:
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
