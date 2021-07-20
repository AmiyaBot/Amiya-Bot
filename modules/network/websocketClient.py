import json
import threading

from modules.network.chainBuilder import Chain
from ws4py.client.threadedclient import WebSocketClient
from modules.automaticAction import run_automatic_action
from message.messageHandler import MessageHandler
from modules.config import get_config


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
        command, content = Chain(self.session, data, message, message_chain, at).content()

        self.send(
            json.dumps(
                {
                    'syncId': 1,
                    'command': command,
                    'subCommand': None,
                    'content': content
                }
            )
        )
