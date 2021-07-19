import json
import threading

from ws4py.client.threadedclient import WebSocketClient
from modules.automaticAction import run_automatic_action
from modules.config import get_config


class Websocket(WebSocketClient):
    def __init__(self, handler=None):
        server = get_config('server')
        self_id = get_config('self_id')

        host = server['server_ip']
        port = server['tcp_port']
        auth = server['auth_key']

        ws = 'ws://%s:%d/all?verifyKey=%s&&qq=%s' % (host, port, auth, self_id)

        super().__init__(ws)
        self.connect()
        self.handler = handler

    def opened(self):
        # 启动循环事件线程
        run_automatic_action()
        print('websocket connecting success')

    def closed(self, code, reason=None):
        print('websocket lose connection')

    def received_message(self, message):
        data = json.loads(str(message))['data']
        if self.handler:
            threading.Timer(0, self.handler, args=(data,)).start()
