import re

from core.resolver.message import Message
from core.resolver.lib.imageManager import ImageManager
from core.resolver.lib.voiceManager import VoiceManager
from core.util.config import reward, config
from core.util.imageCreator import create_image

Image = ImageManager()
Voice = VoiceManager()


class Chain:
    def __init__(self, data: Message, feeling: int = reward.reply.feeling, at: bool = True, quote: bool = False):
        self.data = data
        self.feeling = feeling

        self.chain = []
        self.voices = []
        self.command = 'sendFriendMessage'
        self.target = data.user_id
        self.record = ''

        if self.data.type == 'group':
            self.command = 'sendGroupMessage'
            self.target = data.group_id

            if data.user_id and quote:
                self.quote()
            if data.user_id and at:
                self.at()

    def rec(self, record):
        self.record = record
        return self

    def at(self, user=None, enter=True):
        self.chain.append({
            'type': 'At',
            'target': user or self.data.user_id
        })
        if enter:
            return self.text('\n')
        return self

    def quote(self):
        self.chain.append({
            'type': 'Quote',
            'id': self.data.message_id,
            'senderId': self.data.user_id,
            'targetId': self.data.group_id,
            'groupId': self.data.group_id,
            'origin': self.data.message['messageChain']
        })
        return self

    def text(self, text, trans_image=True):
        chain = []
        r = re.findall(r'(\[face(\d+)])', text)
        if r:
            face = []
            for item in r:
                text = text.replace(item[0], ':face')
                face.append(item[1])

            for index, item in enumerate(text.split(':face')):
                if item != '':
                    chain.append({
                        'type': 'Plain',
                        'text': item
                    })
                if index <= len(face) - 1:
                    chain.append({
                        'type': 'Face',
                        'faceId': face[index]
                    })
        else:
            if trans_image and len(text) >= config.message.transToImageLength:
                self.text_image(text)
            else:
                chain.append({
                    'type': 'Plain',
                    'text': text
                })

        self.chain += chain
        return self

    def text_image(self, text, images=None, title='Common'):
        return self.image(
            path=create_image(text, title, images)
        )

    def image(self, path):
        self.chain.append({
            'type': 'Image',
            'imageId': Image.image(path, self.data.type)
        })
        return self

    def voice(self, path):
        value, is_id = Voice.voice(path, self.data.type)
        field = 'voiceId' if is_id else 'path'
        self.voices.append({
            'type': 'Voice',
            field: value
        })
        return self
