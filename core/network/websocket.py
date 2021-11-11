import abc
import json
import time
import threading

from contextlib import contextmanager
from ws4py.client.threadedclient import WebSocketClient
from core.resolver.messageChain import Chain, Message
from core.asyncio.threadPool import ThreadPool
from core.database.models import User, Message as MessageBase
from core.config import config
from core.util import log


class WebSocket(WebSocketClient):
    def __init__(self):
        server = config.miraiApi
        account = config.account.bot

        host = f'{server.host}:{server.port.ws}'

        super().__init__(f'ws://{host}/all?verifyKey={server.authKey}&&qq={account}')

        self.executor = ThreadPool()
        self.offline = config.setting.offline
        self.account = account
        self.session = None
        self.send_err = True

    def __del__(self):
        try:
            self.close()
        except OSError:
            pass

    def __send(self, data):
        if self.offline is False:
            self.send(data)
        else:
            print(json.loads(data)['content']['messageChain'])

    @abc.abstractmethod
    def on_opened(self):
        pass

    @abc.abstractmethod
    def on_received(self, data):
        pass

    def client_start(self):
        if self.offline:
            msg = 'discontinued starting because config <offline> is "True".'
            log.info(msg)
            raise Exception(msg)

        try:
            self.connect()
            threading.Thread(target=self.run_forever).start()
        except ConnectionRefusedError:
            raise Exception(f'cannot connect websocket server from mirai-api-http.')

    def closed(self, code, reason=None):
        log.info(f'websocket closed [{code}] {str(reason, encoding="utf-8")}')
        self.executor.terminate()

    def received_message(self, message):
        data = json.loads(str(message))

        if 'data' not in data:
            self.close()
            return False

        data = data['data']

        if 'session' in data:
            self.session = data['session']
            self.on_opened()

            log.info('init websocket session: ' + self.session)
            log.info('websocket connect succeeded.')
            return False

        self.executor.put(self.on_received, data, self.traceback_error)

    def traceback_error(self, success, result):
        if success is False and self.send_err:
            self.send_to_admin(result.replace('  ', '    '))

    def send_to_admin(self, message: str):
        with self.send_custom_message(user_id=config.account.admin, _type='friend') as reply:
            reply: Chain
            reply.text(message)

    @contextmanager
    def send_custom_message(self, user_id: int = 0, group_id: int = 0, _type='group'):
        data = Message()

        data.type = _type
        data.user_id = user_id
        data.group_id = group_id

        reply = Chain(data, quote=False)
        yield reply

        self.send_message(reply, update=False)

    def send_message(self, reply: Chain, update: bool = True):
        if update:
            self.update_record(reply)

        if reply.chain:
            self.__send(self.build_message(reply))

        if reply.voices:
            for voice in reply.voices:
                self.__send(
                    self.build_message(Chain(reply.data), chain=[voice])
                )

    def build_message(self, reply: Chain, chain: list = None, sync_id: int = 1):
        content = {
            'target': reply.target,
            'sessionKey': self.session,
            'messageChain': chain or reply.chain
        }

        if reply.quote:
            content['quote'] = reply.data.message_id

        return json.dumps(
            {
                'syncId': sync_id,
                'command': reply.command,
                'subCommand': None,
                'content': content
            },
            ensure_ascii=False
        )

    def update_record(self, reply: Chain):

        user: User = reply.data.user_info if hasattr(reply.data, 'user_info') else User.get_or_none(
            user_id=reply.data.user_id)

        if user is not None:
            user_mood = user.user_mood
            user_mood += reply.feeling
            if user_mood <= 0:
                user_mood = 0
            if user_mood >= 15:
                user_mood = 15

            User.update(
                user_mood=user_mood,
                user_feeling=User.user_feeling + reply.feeling,
                message_num=User.message_num + 1
            ).where(User.user_id == reply.data.user_id).execute()

        MessageBase.create(
            user_id=self.account,
            target_id=reply.data.user_id,
            group_id=reply.data.group_id,
            record=reply.record,
            msg_type=reply.data.type,
            msg_time=int(time.time())
        )
