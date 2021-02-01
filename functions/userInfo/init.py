import json
import random

from database.baseController import BaseController
from message.messageType import MessageType
from modules.resource.voiceManager import VoiceManager
from modules.commonMethods import Reply

from functions.gacha.gacha import GaCha

database = BaseController()
MSG = MessageType()
VM = VoiceManager()

with open('resource/words/voices.json', encoding='utf-8') as voices:
    touch = json.load(voices)['touch']


class Init:
    def __init__(self):
        self.function_id = 'userInfo'
        self.keyword = ['信赖', '关系', '好感', '我的信息', '个人信息']

    def action(self, data):
        user = database.user.get_user(data['user_id'])
        if user:
            feeling = user['user_feeling'] if user['user_feeling'] <= 4000 else 4000

            gc = GaCha(data['user_id'])

            text = '博士，这是您的个人信息\n\n' \
                   '今日{sign}签到\n' \
                   '累计签到：{sign_times}\n' \
                   '累计互动：{message_num}\n' \
                   '阿米娅的信赖：{feeling}%\n' \
                   '阿米娅的心情：{mood}%\n' \
                   '\n【抽卡信息】\n' \
                   '寻访凭证剩余：{coupon}\n' \
                   '{break_even}' \
                .format(sign='已' if user['sign_in'] else '未',
                        sign_times=user['sign_times'],
                        message_num=user['message_num'],
                        feeling=int(feeling / 10),
                        mood=int(user['user_mood'] / 15 * 100),
                        coupon=user['coupon'],
                        break_even=gc.check_break_even())

            voice_list = []
            for item in touch:
                if feeling >= item['feeling']:
                    voice_list.append(item['text'])

            if voice_list:
                text += '\n\n' + random.choice(voice_list)

            return Reply(text, auto_image=False)
        else:
            database.user.update_user(data['user_id'], 0)
            return self.action(data)
