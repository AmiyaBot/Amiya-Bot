import json
import threading

from database.baseController import BaseController
from modules.commonMethods import Reply, restart
from modules.gameData import GameData
from modules.config import get_config

config = get_config()
database = BaseController()
gameData = GameData()


def admin(data):
    message = data['text']
    user_id = data['user_id']

    if user_id == config['admin_id']:
        if '公告' in message:
            database.user.set_waiting(user_id, 'Notice')
            return Reply('正在等待您的公告...')

        if '重启' in message:
            with open('temp/restart_reply.json', mode='w+', encoding='utf-8') as reply:
                reply.write(json.dumps(data, ensure_ascii=False))
            threading.Timer(3, restart).start()
            return Reply('核心准备关闭...即将重新启动...')

        if '更新' in message:
            res = gameData.update()
            if res:
                return Reply(res)
