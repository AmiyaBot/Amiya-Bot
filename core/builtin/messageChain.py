import re
import json

from typing import Union, List
from contextlib import asynccontextmanager
from core.util import read_yaml
from core.builtin.message import Message
from core.builtin.imageCreator import create_image, ImageElem, IMAGES_TYPE
from core.builtin.resourceManager import ResourceManager

config = read_yaml('config/private/bot.yaml')


class Chain:
    def __init__(self, data: Message, at: bool = False, quote: bool = True):
        """
        创建 Mirai 消息链

        :param data:  Message 对象
        :param at:    是否 @ 目标
        :param quote: 是否引用目标消息
        """
        self.data = data
        self.chain = []
        self.voice_list = []
        self.command = 'sendFriendMessage'
        self.target = data.user_id
        self.quote = False

        if self.data.type == 'group':
            self.command = 'sendGroupMessage'
            self.target = data.group_id

            if data.user_id and quote:
                self.quote = True
            if data.user_id and at:
                self.at()

    def __str__(self):
        return f'{self.command}: {self.target}'

    def at(self, user: int = None, enter: bool = True):
        self.chain.append({
            'type': 'At',
            'target': user or self.data.user_id
        })
        if enter:
            return self.text('\n')
        return self

    def text(self, text, enter: bool = False, auto_convert: bool = True):
        chain = []

        if re.findall(r'\[cl\s(.*?)@#(.*?)\scle]', text):
            return self.text_image(text)

        if text.rstrip('\n') != '':
            text = text.rstrip('\n')

        r = re.findall(r'(\[face:(\d+)])', text)
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
            if auto_convert and len(text) >= config.imageCreator.convertLength:
                self.text_image(text)
            else:
                chain.append({
                    'type': 'Plain',
                    'text': text
                })

        self.chain += chain

        if enter:
            return self.text('\n')
        return self

    def text_image(self, text, images: IMAGES_TYPE = None):
        width = 700
        logo = [
            ImageElem('resource/style/rabbit.png', size=30, pos=(width - 30, 0))
        ]
        return self.image(
            path=create_image(text, width=width, max_seat=width - 50, images=(images or []) + logo, bgcolor='#F5F5F5')
        )

    def image(self, path: Union[str, bytes, List[Union[str, bytes]]]):
        if type(path) is not list:
            path = [path]

        for item in path:
            self.chain.append({
                'type': 'Image',
                'path': item,
                'imageId': None
            })
        return self

    def voice(self, path: Union[str, List[str]]):
        if type(path) is str:
            path = [path]

        for item in path:
            self.voice_list.append({
                'type': 'Voice',
                'path': item,
                'voiceId': None
            })
        return self

    async def build(self, session: str, chain: list = None, sync_id: int = 1):

        chain = chain or self.chain
        if chain:
            for item in chain:
                if item['type'] == 'Image' and not item['imageId']:
                    item['imageId'] = await ResourceManager.get_image_id(item['path'], self.data.type)
                    del item['path']
                if item['type'] == 'Voice' and not item['voiceId']:
                    item['voiceId'] = await ResourceManager.get_voice_id(item['path'], self.data.type)
                    del item['path']

        content = {
            'target': self.target,
            'sessionKey': session,
            'messageChain': chain
        }

        if self.quote:
            content['quote'] = self.data.message_id

        return json.dumps(
            {
                'syncId': sync_id,
                'command': self.command,
                'subCommand': None,
                'content': content
            },
            ensure_ascii=False
        )

    @asynccontextmanager
    async def create(self):
        yield self


def custom_chain(user_id: int = 0, group_id: int = 0, msg_type: str = 'group') -> Chain:
    data = Message()

    data.type = msg_type
    data.user_id = user_id
    data.group_id = group_id

    return Chain(data, quote=False)
