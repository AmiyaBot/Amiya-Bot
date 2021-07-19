import json
import threading

from ws4py.client.threadedclient import WebSocketClient
from modules.automaticAction import run_automatic_action
from database.baseController import BaseController
from message.messageHandler import MessageHandler
from modules.config import get_config

database = BaseController()


class Websocket(WebSocketClient):
    def __init__(self):
        self.self_id = get_config('self_id')

        server = get_config('server')
        host = server['server_ip']
        port = server['tcp_port']
        auth = server['auth_key']

        ws = 'ws://%s:%d/all?verifyKey=%s&&qq=%s' % (host, port, auth, self.self_id)

        super().__init__(ws)

        self.connect()
        self.handler = MessageHandler(self)
        self.session = None

    def opened(self):
        # 启动循环事件线程
        run_automatic_action()
        print('websocket connecting success')

    def closed(self, code, reason=None):
        print('websocket lose connection')

    def received_message(self, message):
        data = json.loads(str(message))['data']

        if 'session' in data:
            self.session = data['session']
            print('websocket session init success.')
            return False

        if self.handler:
            threading.Timer(0, self.handler.on_message, args=(data,)).start()

    def send_message(self, data, message='', message_chain=None, at=False):
        database.message.add_message(
            msg_type='reply',
            user_id=self.self_id,
            reply_user=data['user_id']
        )

        if data['type'] == 'group':
            content = self.send_group_message(data, message=message, message_chain=message_chain, at=at)
        else:
            content = self.send_private_message(data, message=message, message_chain=message_chain)

        self.send(
            json.dumps(
                {
                    'syncId': 1,
                    'command': 'sendGroupMessage' if data['type'] == 'group' else 'sendFriendMessage',
                    'subCommand': None,
                    'content': content
                }
            )
        )

    def send_private_message(self, data, message='', message_chain=None):
        if message_chain and type(message_chain) is list:
            chain = message_chain
        else:
            chain = [{
                'type': 'Plain',
                'text': message
            }]

        return {
            'sessionKey': self.session,
            'target': data['user_id'],
            'messageChain': chain
        }

    def send_group_message(self, data, message='', message_chain=None, at=False):
        if message_chain and type(message_chain) is list:
            chain = message_chain
        else:
            chain = [{
                'type': 'Plain',
                'text': message
            }]
        if at:
            at_chain = {'type': 'AtAll', 'target': 0} if at == 'all' else {'type': 'At', 'target': data['user_id']}
            chain.insert(0, {'type': 'Plain', 'text': '\n'})
            chain.insert(0, at_chain)

        return {
            'sessionKey': self.session,
            'target': data['group_id'],
            'messageChain': chain
        }
