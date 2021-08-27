import re
import time

from core import Message, Chain
from core.database.models import Intellect
from handlers.funcInterface import FuncInterface


class IntellectAlarm(FuncInterface):
    def __init__(self):
        super().__init__(function_id='intellectAlarm')

    @FuncInterface.is_disable
    def check(self, data: Message):
        for item in ['理智']:
            if item in data.text:
                return True
        return False

    @FuncInterface.is_used
    def action(self, data: Message):
        message = data.text_digits
        reply = Chain(data)

        r = re.search(re.compile(r'理智(\d+)满(\d+)'), message)
        if r:
            cur_num = int(r.group(1))
            full_num = int(r.group(2))

            if cur_num < 0 or full_num <= 0:
                return Reply('啊这…看来博士是真的没有理智了……回头问问可露希尔能不能多给点理智合剂……')
            if cur_num >= full_num:
                return Reply('阿米娅已经帮博士记…呜……阿米娅现在可以提醒博士了吗')
            if full_num > 135:
                return Reply('博士的理智有这么高吗？')

            full_time = (full_num - cur_num) * 6 * 60 + int(time.time())

            Intellect.insert(
                user_id=data.user_id,
                cur_num=cur_num,
                full_num=full_num,
                full_time=full_time,
                message_type=data.type,
                group_id=data.group_id,
                in_time=int(time.time()),
                status=0
            ).on_conflict(
                conflict_target=[Intellect.user_id],
                preserve=[
                    Intellect.cur_num,
                    Intellect.full_num,
                    Intellect.full_time,
                    Intellect.message_type,
                    Intellect.group_id,
                    Intellect.in_time,
                    Intellect.status
                ]
            ).execute()
            return reply.text('阿米娅已经帮博士记住了，回复满的时候阿米娅会提醒博士的哦～')

        r_list = [
            '多少理智',
            '理智.*多少'
        ]
        for item in r_list:
            r = re.search(re.compile(item), message)
            if r:
                info: Intellect = Intellect.get_or_none(data.user_id)
                if info:
                    full_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(info.full_time))
                    through = int(time.time()) - info.in_time
                    restored = int(through / 360) + info.cur_num

                    text = '博士，根据上一次记录，您的 %d 理智会在 %s 左右回复满\n' \
                           '不计算上限的话，现在已经回复到 %d 理智了' % (info.full_num, full_time, restored)
                    return reply.text(text)
                else:
                    return reply.text('阿米娅还没有帮博士记录理智提醒哦')
