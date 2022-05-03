import re
import asyncio

from typing import Union, List
from contextlib import asynccontextmanager

from core.network.mirai import get_func_name
from core.network.mirai.websoketCommand import WebsocketCommand
from core.util import read_yaml
from core.builtin.message import Message
from core.builtin.imageCreator import create_image, ImageElem, IMAGES_TYPE
from core.builtin.htmlConverter import ChromiumBrowser
from core.builtin.resourceManager import ResourceManager
from core import log

config = read_yaml('config/private/bot.yaml')

IMAGE_WIDTH = 700
PADDING = 10
MAX_SEAT = IMAGE_WIDTH - PADDING * 2


class Chain:
    def __init__(self, data: Message, at: bool = True, quote: bool = False):
        """
        创建 Mirai 消息链

        :param data:  Message 对象
        :param at:    是否 @ 目标
        :param quote: 是否引用目标消息
        """
        self.data = data
        self.chain = []
        self.voice_list = []
        self.command = WebsocketCommand.MessageSend.SendFriendMessage
        self.target = data.user_id
        self.quote = False

        if self.data.type == 'group':
            self.command = WebsocketCommand.MessageSend.SendGroupMessage
            self.target = data.group_id

            if data.user_id and quote:
                self.quote = True
            if data.user_id and at:
                self.at(enter=True)

    def __str__(self):
        return f'{get_func_name(self.command)}: {self.target}'

    def at(self, user: int = None, enter: bool = False):
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

    def text_image(self,
                   text,
                   images: IMAGES_TYPE = None,
                   width: int = None,
                   height: int = None):
        logo = [
            ImageElem('resource/style/rabbit.png', size=20, pos=(-20, 0))
        ]
        return self.image(target=create_image(text,
                                              images=(images or []) + logo,
                                              width=width,
                                              height=height,
                                              padding=PADDING,
                                              max_seat=MAX_SEAT,
                                              bgcolor='#F5F5F5'))

    def image(self, target: Union[str, bytes, List[Union[str, bytes]]]):
        if type(target) is not list:
            target = [target]

        for item in target:
            self.chain.append({
                'type': 'Image',
                'path': item
            })
        return self

    def voice(self, target: Union[str, List[str]]):
        if type(target) is str:
            target = [target]

        for item in target:
            self.voice_list.append({
                'type': 'Voice',
                'path': item
            })
        return self

    def html(self, path: str, data: Union[dict, list] = None, is_template: bool = True):
        self.chain.append({
            'type': 'Html',
            'data': data,
            'template': f'template/{path}' if is_template else path,
            'is_file': is_template
        })
        return self

    async def build(self, session: str, chain: list = None, sync_id: int = 1):

        chain = chain or self.chain
        chain_data = []

        if chain:
            for item in chain:
                if item['type'] == 'Image':
                    chain_data.append({
                        'type': 'Image',
                        'imageId': await ResourceManager.get_image_id(item['path'], self.data.type)
                    })
                    continue

                if item['type'] == 'Voice':
                    chain_data.append({
                        'type': 'Voice',
                        'voiceId': await ResourceManager.get_voice_id(item['path'], self.data.type)
                    })
                    continue

                if item['type'] == 'Html':
                    async with log.catch('html convert error:'):
                        browser = ChromiumBrowser()
                        page = await browser.open_page(item['template'], is_file=item['is_file'])

                        if item['data']:
                            await page.init_data(item['data'])
                            await asyncio.sleep(0.2)

                        chain_data.append({
                            'type': 'Image',
                            'imageId': await ResourceManager.get_image_id(await page.make_image(), self.data.type)
                        })
                        await page.close()
                    continue

                chain_data.append(item)

        if self.quote:
            return self.command(session, self.target, chain_data, quoteMessageId=self.data.message_id, syncId=sync_id)
        return self.command(session, self.target, chain_data, syncId=sync_id)

    @asynccontextmanager
    async def create(self):
        yield self


def custom_chain(user_id: int = 0,
                 group_id: int = 0,
                 msg_type: str = 'group') -> Chain:
    """
    自定义消息体，可以在没有 Message 对象的场景下使用

    :param user_id:  用户ID
    :param group_id: 群组ID
    :param msg_type: 消息类型
    :return:         Chain 对象
    """
    data = Message()

    data.type = msg_type
    data.user_id = user_id
    data.group_id = group_id

    return Chain(data)
