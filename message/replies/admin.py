import re
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

        if '屏蔽' in message:
            r = re.search(r'(\d+)', message)
            if r:
                user_id = r.group(1)
                user = database.user.get_user(user_id)
                if user:
                    database.user.set_black_user(user_id)
                    return Reply('已屏蔽用户【%s】，但为什么要这么做呢...' % user_id)
                else:
                    return Reply('没有找到用户【%s】' % user_id)

        if '更新' in message:
            res = gameData.update()
            if res:
                return Reply(res)
