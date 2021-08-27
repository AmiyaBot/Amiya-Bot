import abc
import json
import time

from ws4py.client.threadedclient import WebSocketClient
from core.resolver.messageChain import Chain, Message
from core.thread.threadPool import ThreadPool
from core.database.models import User, Message as MessageBase
from core.util.config import config
from core.util import log


class WebSocket(WebSocketClient):
    def __init__(self):
        server = config('server')
        account = config('selfId')

        host = f'{server["serverIp"]}:{server["websocketPort"]}'

        super().__init__(f'ws://{host}/all?verifyKey={server["authKey"]}&&qq={account}')

        self.executor = ThreadPool()
        self.offline = config('offline')
        self.account = account
        self.session = None
        self.send_err = True

    def __del__(self):
        try:
            self.close()
        except OSError:
            pass

    @abc.abstractmethod
    def handler(self, data):
        pass

    def start(self):
        if self.offline:
            msg = 'discontinued starting because config <offline> is "True".'
            log.info(msg)
            raise Exception(msg)

        try:
            self.connect()
            self.run_forever()
        except KeyboardInterrupt:
            return False
        except ConnectionRefusedError:
            pass

        raise Exception(f'cannot connect websocket server from mirai-api-http.')

    def closed(self, code, reason=None):
        log.info(f'websocket closed [{code}] {reason}')
        self.executor.terminate()

    def received_message(self, message):
        data = json.loads(str(message))['data']

        if 'session' in data:
            self.session = data['session']
            log.info('init websocket session: ' + self.session)
            log.info('websocket connect succeeded.')
            return False

        self.executor.put(self.handler, data, self.traceback_error)

    def traceback_error(self, success, result):
        if success is False and self.send_err:
            self.send_to_admin(result.replace('  ', '    '))

    def send_to_admin(self, message: str):
        self.send_to_user(message, user_id=config('adminId'), _type='friend')

    def send_to_user(self, message: str, user_id: int, group_id: int = 0, _type='group'):
        data = Message()

        data.type = _type
        data.user_id = user_id
        data.group_id = group_id

        self.send_message(Chain(data).text(message))

    def send_message(self, reply: Chain, sync_id: int = 1):
        msg = json.dumps(
            {
                'syncId': sync_id,
                'command': reply.command,
                'subCommand': None,
                'content': {
                    'sessionKey': self.session,
                    'target': reply.target,
                    'messageChain': reply.chain
                }
            }
        )

        MessageBase.create(
            user_id=self.account,
            target_id=reply.data.user_id,
            group_id=reply.data.group_id,
            record=reply.record,
            msg_type=reply.data.type,
            msg_time=int(time.time())
        )
        User.update(
            user_feeling=User.user_feeling + reply.feeling,
            message_num=User.message_num + 1
        ).where(User.user_id == reply.data.user_id).execute()

        if self.offline is False:
            self.send(msg)
        else:
            log.info('--> ' + json.dumps(reply.chain, ensure_ascii=False))
