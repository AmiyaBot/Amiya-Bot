import re
import threading

from database.baseController import BaseController
from modules.commonMethods import Reply, restart
from modules.dataSource.gameData import GameData
from modules.config import get_config

admin_id = get_config('admin_id')
database = BaseController()
gameData = GameData()


def admin(data):
    message = data['text']
    user_id = data['user_id']

    if user_id == admin_id:
        if '更新全部' in message:
            return Reply(gameData.update())

        if '更新图片' in message:
            avatars, photo, skills, skins = gameData.save_operator_photo()
            enemies = gameData.save_enemies_photo()
            return Reply('更新了'
                         '\n -- %s 个干员头像'
                         '\n -- %s 张干员半身照'
                         '\n -- %s 个技能图标'
                         '\n -- %s 张干员皮肤'
                         '\n -- %s 张敌人图片' % (avatars, photo, skills, skins, enemies))

        if '公告' in message:
            database.user.set_waiting(user_id, 'Notice')
            return Reply('正在等待您的公告...')

        if '重启' in message:
            threading.Timer(3, restart).start()
            return Reply('即将重新启动...')

        if '屏蔽' in message:
            r = re.search(r'(\d+)', message)
            if r:
                mute_id = int(r.group(1))
                if mute_id == user_id:
                    return Reply('不能屏蔽您自己...')
                user = database.user.get_user(mute_id)
                if user:
                    database.user.set_black_user(mute_id)
                    return Reply('已屏蔽用户【%s】' % mute_id)
                else:
                    return Reply('没有找到用户【%s】' % mute_id)
