from modules.config import get_config
import requests
import threading

from modules.network.websocketClient import Websocket
from modules.network.httpRequests import HttpRequests
from message.messageHandler import MessageHandler

message = MessageHandler()
config=get_config()
verifyCode=config["server"]["auth_key"]
self_qq=config["self_id"]


def start():
    
    websocket = Websocket(verify=verifyCode,qqid=self_qq, handler=message.on_message)
    threading.Thread(target=websocket.run_forever).start()


if __name__ == '__main__':
    start()
