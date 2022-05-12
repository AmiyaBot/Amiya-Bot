import re
import time

from typing import List
from core import bot, websocket, Message, Chain, custom_chain
from core.database.user import Intellect


async def verify(data: Message):
    return (True, 2) if '理智' in data.text and ('满' in data.text or '多少' in data.text) else False


@bot.on_group_message(function_id='intellectAlarm', verify=verify)
async def _(data: Message):
    message = data.text_digits
    reply = Chain(data)

    r = re.search(re.compile(r'理智(\d+)满(\d+)'), message)
    if r:
        cur_num = int(r.group(1))
        full_num = int(r.group(2))

        if cur_num < 0 or full_num <= 0:
            return reply.text('啊这…看来博士是真的没有理智了……回头问问可露希尔能不能多给点理智合剂……')
        if cur_num >= full_num:
            return reply.text('阿米娅已经帮博士记…呜……阿米娅现在可以提醒博士了吗')
        if full_num > 135:
            return reply.text('博士的理智有这么高吗？')

        full_time = (full_num - cur_num) * 6 * 60 + int(time.time())

        Intellect.insert_or_update(
            insert={
                'user_id': data.user_id,
                'cur_num': cur_num,
                'full_num': full_num,
                'full_time': full_time,
                'message_type': data.type,
                'group_id': data.group_id,
                'in_time': int(time.time()),
                'status': 0
            },
            preserve=[
                Intellect.cur_num,
                Intellect.full_num,
                Intellect.full_time,
                Intellect.message_type,
                Intellect.group_id,
                Intellect.in_time,
                Intellect.status
            ],
            conflict_target=[Intellect.user_id]
        )
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

                text = f'博士，根据上一次记录，您的 {info.full_num} 理智会在 {full_time} 左右回复满\n' \
                       f'不计算上限的话，现在已经回复到 {restored} 理智了'

                return reply.text(text)
            else:
                return reply.text('阿米娅还没有帮博士记录理智提醒哦')


@bot.timed_task(each=10)
async def _():
    conditions = (Intellect.status == 0, Intellect.full_time <= int(time.time()))
    results: List[Intellect] = Intellect.select().where(*conditions)
    if results:
        Intellect.update(status=1).where(*conditions).execute()
        for item in results:
            text = f'博士！博士！您的理智已经满 {item.full_num} 了，快点上线查看吧～'

            data = custom_chain(int(item.user_id), int(item.group_id), item.message_type)
            data.at(enter=True).text(text)

            await websocket.send_message(data)
