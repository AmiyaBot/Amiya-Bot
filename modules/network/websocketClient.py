import json
import threading

from ws4py.client.threadedclient import WebSocketClient
from modules.automaticAction import run_automatic_action
from modules.config import get_config

class Websocket(WebSocketClient):
    

    def __init__(self,verify=None,qqid:int=None, session=None, handler=None):
        server = get_config('server')

        host = server['server_ip']
        port = server['server_port']
        super().__init__('ws://%s:%d/all?verifyKey=%s&qq=%s' % (host, port, verify,qqid))
        self.connect()
        self.handler = handler

        self.inited=False

    def opened(self):
        # 启动循环事件线程
        
        print('websocket connecting success')

    def closed(self, code, reason=None):
        print('websocket lose connection')

    def received_message(self, message):
        data = json.loads(str(message))

        if not self.inited:
            session=data["data"]["session"]
            with open("temp/session.txt",'w')as f:
                f.write(session)
            self.inited=True
            print(f"session loaded: {session}")
            run_automatic_action()
            return
        else:
            if self.handler:
                threading.Timer(0, self.handler, args=(data,)).start()

class WebSocketLinker(object):
    def __init__(self,ws:Websocket):
        self.ws=ws
    
    