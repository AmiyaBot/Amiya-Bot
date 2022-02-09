import json
import time
import asyncio
import websockets

from contextlib import asynccontextmanager
from core.network import WSOpration
from core.database.messages import MessageRecord
from core.builtin.message import WaitEventCancel
from core.builtin.messageChain import Chain, custom_chain
from core.builtin.message.mirai import Mirai
from core.builtin.messageHandler import message_handler
from core.control import StateControl
from core.config import config
from core.util import singleton
from core import log

host = config.miraiApiHttp.host
port = config.miraiApiHttp.port.ws
auth_key = config.miraiApiHttp.authKey
account = config.miraiApiHttp.account


@singleton
class WebsocketClient(WSOpration):
    def __init__(self):
        self.url = f'ws://{host}:{port}/all?verifyKey={auth_key}&&qq={account}'
        self.connect = None
        self.session = None

    async def connect_websocket(self):
        try:
            async with websockets.connect(self.url) as websocket:
                log.info('websocket connect successful. waiting handshake...')
                self.connect = websocket
                while StateControl.alive:
                    message = await websocket.recv()

                    if message == b'':
                        await websocket.close()
                        return False

                    asyncio.create_task(
                        self.handle_message(str(message))
                    )

                await websocket.close()

                log.info('websocket closed.')

        except websockets.ConnectionClosedOK as e:
            log.error(f'websocket connection closed. {e}')
        except ConnectionRefusedError:
            log.error('cannot connect to mirai-api-http websocket server.')

    async def send(self, reply: Chain):
        if reply.chain:
            await self.connect.send(await reply.build(self.session))

        if reply.voice_list:
            reply.quote = False
            for voice in reply.voice_list:
                await self.connect.send(
                    await reply.build(self.session, chain=[voice])
                )

        MessageRecord.create(
            user_id=account,
            group_id=reply.data.group_id,
            msg_type=reply.data.type,
            message=json.dumps(reply.chain, ensure_ascii=False),
            classify='reply',
            create_time=int(time.time())
        )

    @asynccontextmanager
    async def send_to_admin(self):
        data = custom_chain(msg_type='friend')

        yield data

        for item in config.admin.accounts:
            data.target = item

            await self.send(data)

    async def handle_message(self, message: str):
        async with log.catch(handler=self.handle_error, ignore=[KeyError, WaitEventCancel, json.JSONDecodeError]):

            data = json.loads(message)
            data = data['data']

            if 'session' in data:
                self.session = data['session']
                log.info('websocket handshake successful. session: ' + self.session)
                return False

            message_data = Mirai.mirai_message_formatter(account, data, self)
            if message_data:
                await message_handler(message_data, self)

    async def handle_error(self, message: str):
        if not self.session:
            return

        async with self.send_to_admin() as chain:
            chain.text(message.replace('  ', '    '))
