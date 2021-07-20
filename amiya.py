import requests
import threading

from modules.network.websocketClient import Websocket
from modules.network.httpRequests import HttpRequests


def start():
    try:
        # 请求更新 session
        HttpRequests().init_session()
        print('http session init success.')
    except requests.exceptions.ConnectionError:
        # 请求失败则重试
        print('server not found.')
        start()
    else:
        # 连接 websocket 服务
        threading.Thread(target=Websocket().run_forever).start()


if __name__ == '__main__':
    start()
