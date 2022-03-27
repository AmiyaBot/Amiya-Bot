import time
import asyncio
import functions

from abc import ABC
from core.network import WSOperation
from core.builtin.message.mirai import mirai_message_formatter
from core.builtin.messageHandler import message_handler
from core.config import config
from core.util import read_yaml, create_dir
from core.bot import BotHandlers, Chain
from core import log, initialization

BotHandlers.add_prefix(
    read_yaml('config/private/talking.yaml').call.positive
)


class Simulation(WSOperation, ABC):
    async def send(self, reply: Chain):
        for item in reply.chain + reply.voice_list:
            if item['type'] == 'Plain':
                print('text: ', item['text'].strip('\n'))

            if item['type'] == 'Voice':
                print('voice: ', item['path'])

            if item['type'] == 'Image':
                if type(item['path']) is bytes:
                    png = f'fileStorage/test/{int(time.time())}.png'

                    create_dir(png, is_file=True)
                    with open(png, mode='wb') as file:
                        file.write(item['path'])
                        print('image: ', png)
                else:
                    print('image: ', item['path'])


async def test():
    log.info(
        [
            f'starting Amiya-Bot Testing...',
            f'%d function module(s) loaded.' % len([f for f in dir(functions) if f[:2] != '__'])
        ] + BotHandlers.detail()
    )

    await initialization()

    log.info('testing ready, please input the message text.')

    while True:
        await asyncio.sleep(0)
        data = message(input())
        await message_handler(data, Simulation())


def message(text, _type='group'):
    mirai_text = {
        'type': 'GroupMessage' if _type == 'group' else 'FriendMessage',
        'messageChain': [
            {
                'type': 'Plain',
                'text': text
            }
        ],
        'sender': {
            'id': config.admin.accounts[0],
            'permission': 'OWNER',
            'nickname': 'OWNER',
            'memberName': 'OWNER',
            'remark': 'none',
            'group': {
                'id': config.test.group[0]
            }
        }
    }
    return mirai_message_formatter(account=config.miraiApiHttp.account, data=mirai_text, operation=Simulation())


if __name__ == '__main__':
    asyncio.run(test())
