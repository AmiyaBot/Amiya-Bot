import re
import time
import datetime

from database.baseController import BaseController
from functions.functionQuery.function import Function
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

        if '功能' in message:
            for item in Function.index_reg:
                r = re.search(re.compile(item), message)
                if r:
                    index = int(r.group(1))
                    if 0 < index <= len(Function.function_list):
                        index -= 1
                        func = Function.function_list[index]
                        if func['id']:
                            group = Function.function_groups[func['id']]

                            status = 0
                            if word_in_sentence(message, ['关闭', '禁用']):
                                status = 1
                            if word_in_sentence(message, ['打开', '开启']):
                                status = 2

                            if status:
                                database.function.set_disable_function(group_id, func['id'], status == 1)

                                text = '已在本群%s以下功能：\n\n' % ('关闭' if status == 1 else '打开')
                                text += '\n'.join([('  --  ' + n) for n in group])

                                return Reply(text, auto_image=False)
                        else:
                            return Reply('【%s】功能不可操作' % func['title'])
