import time
import re

from database.baseController import BaseController
from modules.commonMethods import Reply

database = BaseController()


class Init:
    def __init__(self):
        self.function_id = 'intellectFullAlarm'
        self.keyword = ['理智']

    @staticmethod
    def action(data):

        message = data['text_digits']

        r = re.search(re.compile(r'理智(\d+)满(\d+)'), message)
        if r:
            num1 = int(r.group(1))
            num2 = int(r.group(2))
            if num1 < 0 or num2 <= 0:
                return Reply('啊这…看来博士是真的没有理智了……回头问一下可露希尔能不能多给点理智合剂……')
            if num1 >= num2:
                return Reply('阿米娅已经帮博士记……啊这…阿米娅现在可以提醒博士了吗')
            if num2 > 135:
                return Reply('博士的理智上限有这么高吗？')
            full_time = (num2 - num1) * 6 * 60 + int(time.time())
            target_id = data['group_id'] if data['type'] == 'group' else 0
            database.remind.add_intellect_full_alarm(
                data['user_id'],
                num1,
                num2,
                full_time,
                data['type'],
                target_id
            )
            return Reply('阿米娅已经帮博士记住了，回复满的时候阿米娅会提醒博士的哦～')

        r_list = [
            '多少理智',
            '理智.*多少'
        ]
        for item in r_list:
            r = re.search(re.compile(item), message)
            if r:
                info = database.remind.check_intellect_by_user(data['user_id'])
                if info:
                    full_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(info['full_time']))
                    through = int(time.time()) - info['in_time']
                    restored = int(through / 360) + info['cur_num']

                    text = '博士，根据上一次记录，您的 %d 理智会在 %s 左右回复满\n' \
                           '不计算上限的话，现在已经回复到 %d 理智了' % (info['full_num'], full_time, restored)
                    return Reply(text)
                else:
                    return Reply('阿米娅还没有帮博士记录理智提醒哦')
