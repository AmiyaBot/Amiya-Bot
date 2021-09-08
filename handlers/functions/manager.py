import time

from core import Message, Chain
from core.database.models import GroupSleep
from core.util.common import word_in_sentence, calc_time_total


def manager_handler(data: Message):
    message = data.text
    reply = Chain(data)

    if data.is_call and (data.is_admin or data.is_group_admin):
        if word_in_sentence(message, ['休息', '下班']):
            if data.group_info.active == 1:
                GroupSleep.update(active=0, sleep_time=int(time.time())).where(GroupSleep.group_id == data.group_id).execute()
                return reply.text('阿米娅打卡下班啦，博士需要阿米娅的时候再让阿米娅工作吧。^_^')

        if word_in_sentence(message, ['工作', '上班']):
            if data.group_info.active == 0:
                seconds = int(time.time()) - int(data.group_info.sleep_time)
                total = calc_time_total(seconds)
                text = '打卡上班啦~阿米娅%s休息了%s……' % ('才' if seconds < 600 else '一共', total)
                if seconds < 600:
                    text += '\n博士真是太过分了！哼~ >.<'
                else:
                    text += '\n充足的休息才能更好的工作，博士，不要忘记休息哦 ^_^'

                GroupSleep.update(active=1, sleep_time=0).where(GroupSleep.group_id == data.group_id).execute()
                return reply.text(text)
            else:
                return reply.text('阿米娅没有偷懒哦博士，请您也不要偷懒~')

    return data.group_info.active == 1
