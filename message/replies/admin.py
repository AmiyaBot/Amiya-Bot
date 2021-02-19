import json
import threading

from database.baseController import BaseController
from modules.commonMethods import Reply, restart

with open('config.json') as config:
    config = json.load(config)

database = BaseController()


def admin(data):
    message = data['text']
    user_id = data['user_id']

    if user_id == config['admin_id']:
        if '公告' in message:
            database.user.set_waiting(user_id, 'Notice')
            return Reply('正在等待您的公告...')

        if '重启' in message:
            threading.Timer(5, restart).start()
            return Reply('即将在 5 秒后重新启动~')
