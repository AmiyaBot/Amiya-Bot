import os
import json
import requests
import threading

from modules.network.websocketClient import Websocket
from modules.network.httpRequests import HttpRequests
from message.messageHandler import MessageHandler
from modules.miraiProcess import Process

message = MessageHandler()
http = HttpRequests()


def start():
    try:
        # 请求更新 session
        http.init_session()
        print('Session init success.')
    except requests.exceptions.ConnectionError:
        # 请求失败则重试
        print('Server not found.')
        start()
    else:
        # 连接 websocket 服务
        session = http.get_session()
        websocket = Websocket(session, handler=message.on_message)
        threading.Thread(target=websocket.run_forever).start()


if __name__ == '__main__':
    with open('config.json', encoding='utf-8') as config:
        config = json.load(config)

    # 启动 mirai-console 进程
    mirai = Process(os.path.dirname(os.path.abspath(__file__)) + '\\console')
    mirai.init_auto_login(config['self_id'], config['self_passwords'])
    mirai.start_process()

    # 启动 Amiya 进程，预留时间供 console 启动
    threading.Timer(15, start).start()
