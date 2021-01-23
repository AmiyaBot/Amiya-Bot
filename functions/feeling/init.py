import json

from database.baseController import BaseController
from message.messageType import MessageType
from modules.resource.voiceManager import VoiceManager
from modules.commonMethods import Reply

database = BaseController()
MSG = MessageType()
VM = VoiceManager()

with open('resource/words/voices.json', encoding='utf-8') as voices:
    touch = json.load(voices)['touch']


class Init:
    def __init__(self):
        self.function_id = 'feeling'
        self.keyword = ['信赖', '关系', '好感']

    @staticmethod
    def action(data):
        result = database.user.get_user(data['user_id'])
        if result:
            feeling = result[1] if result[1] <= 4000 else 4000

            text = '阿米娅和博士的当前信赖值是: %d%s\n' % (int(feeling / 10), '%')
            voice = ''

            for item in touch:
                if feeling >= item['feeling']:
                    text += item['text']
                    voice = item['voice']
                    break

            # voice = VM.find_voice_id(voice)

            return Reply(text, auto_image=False)
            # return [Reply(text), Reply([MSG.voice(voice)], 0)]
        else:
            return Reply('博士还没有和阿米娅互动过呢～和阿米娅说【阿米娅会什么】来和阿米娅互动吧～')
