import json
import threading

from ws4py.client.threadedclient import WebSocketClient

with open('config.json') as file:
    config = json.load(file)


class Websocket(WebSocketClient):
    def __init__(self, session, handler=None):
        super().__init__(
            'ws://%s:%d/all?sessionKey=%s' % (config['server']['server_ip'], config['server']['server_port'], session))
        self.connect()
        self.handler = handler

    def opened(self):
        print('websocket connecting success')

    def closed(self, code, reason=None):
        print('websocket lose connection')

    def received_message(self, message):
        data = json.loads(str(message))
        if self.handler:
            threading.Timer(0, self.handler, args=(data,)).start()
