import time
import datetime

from database.baseController import BaseController
from modules.commonMethods import Reply, word_in_sentence, calc_time_total
from modules.config import get_config

admin_id = get_config('admin_id')
database = BaseController()


def group_admin(data):
    permission = data['permission']
    group_id = data['group_id']
    user_id = data['user_id']
    message = data['text']

    if permission in ['OWNER', 'ADMINISTRATOR'] or user_id == admin_id:

        if word_in_sentence(message, ['休息', '下班']):
            res = database.group.get_status(group_id)
            if not res or res['active'] == 1:
                database.group.set_status(group_id, 0, int(time.time()))
                return Reply('阿米娅打卡下班啦，博士需要阿米娅的时候再让阿米娅工作吧。^_^')

        if word_in_sentence(message, ['工作', '上班']):
            res = database.group.get_status(group_id)
            if res and res['active'] == 0:
                seconds = int(time.time()) - int(res['sleep_time'])
                total = calc_time_total(seconds)
                text = '打卡上班啦~阿米娅%s休息了%s……' % ('才' if seconds < 600 else '一共', total)
                if seconds < 600:
                    text += '\n博士真是太过分了！哼~ >.<'
                else:
                    text += '\n充足的休息才能更好的工作，博士，不要忘记休息哦 ^_^'

                database.group.set_status(group_id, 1, 0)
                return Reply(text)
            else:
                return Reply('阿米娅没有偷懒哦博士，请您也不要偷懒~')
