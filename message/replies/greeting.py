import json

from database.baseController import BaseController
from message.messageType import MessageType
from modules.resource.voiceManager import VoiceManager
from modules.commonMethods import Reply, talk_time, word_in_sentence

database = BaseController()
MSG = MessageType()
VM = VoiceManager()

with open('resource/words/amiyaName.json', encoding='utf-8') as file:
    amiya_name = json.load(file)


def greeting(data):
    message = data['text']
    nickname = data['nickname']

    for item in ['不能休息', '不能停', '不要休息', '不要停', '很多事情']:
        if item in message:
            return Reply([MSG.voice(VM.find_voice_id('阿米娅_闲置'))])

    for item in ['早上好', '早安', '中午好', '午安', '下午好', '晚上好']:
        if item in message:
            hour = talk_time()
            chain = []
            if hour:
                chain.append(MSG.text('Dr.%s，%s好～' % (nickname, hour)))
            else:
                chain.append(MSG.text('Dr.%s，这么晚还不睡吗？要注意休息哦～' % nickname))
            sign_result = sign_in(data)
            if sign_result:
                chain.append(MSG.text('\n'))
                chain.append(MSG.text(sign_result))
            return Reply(chain, 50 if sign_result else 2, 1 if sign_result else 0)

    if '签到' in message and word_in_sentence(message, amiya_name[0]):
        sign_result = sign_in(data, 1)
        if sign_result:
            return Reply(sign_result, 50, 1, True)

    if '晚安' in message:
        return Reply('Dr.%s，晚安～' % nickname)

    for name in amiya_name[1]:
        if message.find(name) == 0:
            return Reply('哼！Dr.%s不许叫人家%s，不然人家要生气了！' % (nickname, name), -3)


def sign_in(data, sign_type=0):
    user_id = data['user_id']
    user = database.user.get_user(user_id)
    if bool(user) is False:
        database.user.add_feeling(user_id, 15, False)
    if bool(user) is False or user[6] == 0:
        database.user.add_coupon(user_id, 50)
        return '签到成功，50张寻访凭证已经送到博士的办公室啦，请博士注意查收哦'
    if sign_type and user[6] == 1:
        return '博士今天已经签过到了哦'
    return False
