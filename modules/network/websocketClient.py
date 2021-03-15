import json
import threading

from ws4py.client.threadedclient import WebSocketClient
from modules.automaticAction import run_automatic_action
from modules.config import get_config


class Websocket(WebSocketClient):
    def __init__(self, session, handler=None):
        config = get_config()

        host = config['server']['server_ip']
        port = config['server']['server_port']
        super().__init__('ws://%s:%d/all?sessionKey=%s' % (host, port, session))
        self.connect()
        self.handler = handler

    def opened(self):
        # 启动循环事件线程
        run_automatic_action()
        print('websocket connecting success')

    def closed(self, code, reason=None):
        print('websocket lose connection')

    def received_message(self, message):
        data = json.loads(str(message))
        if self.handler:
            threading.Timer(0, self.handler, args=(data,)).start()
