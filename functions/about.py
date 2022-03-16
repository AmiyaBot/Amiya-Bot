import re
import os
import psutil

from typing import List
from core import bot, Message, Chain
from core.util import read_yaml
from core.database.bot import DisabledFunction

func_titles = read_yaml('config/private/functions.yaml', _dict=True)


@bot.on_group_message(keywords=['关闭功能', '开启功能', '打开功能'])
async def _(data: Message):
    if not data.is_admin and not data.is_group_admin:
        return None

    disabled: List[DisabledFunction] = DisabledFunction.select().where(DisabledFunction.group_id == data.group_id)
    disabled: List[str] = [item.function_id for item in disabled]

    status = 0
    if '关闭' in data.text:
        status = 1
    if '开启' in data.text:
        status = 2

    text = '博士，这是可开关的功能列表\n\n已关闭的功能将标记为[cl 红色@#ff0000 cle]\n\n'
    func = {}

    for item in bot.BotHandlers.group_message_handlers:
        if not item.function_id or item.function_id == 'admin':
            continue

        title = func_titles[item.function_id] if item.function_id in func_titles else item.function_id

        if item.function_id not in func:
            func[item.function_id] = [item.function_id, title, 0,
                                      'ff0000' if item.function_id in disabled else '000000']
        func[item.function_id][2] += 1

    func_list = sorted([item for _, item in func.items()], key=lambda n: n[1])

    for index, item in enumerate(func_list):
        text += '[cl 【{index}】{title}, 共 {count} 个相关功能 @#{color} cle]\n'.format(**{
            'index': index + 1,
            'title': item[1],
            'count': item[2],
            'color': item[3]
        })

    wait = await data.waiting(Chain(data).text_image(text).text('回复【序号】%s对应功能' % ('关闭' if status == 1 else '打开')))
    if wait:
        r = re.search(r'(\d+)', wait.text_digits)
        if r:
            index = abs(int(r.group(1))) - 1
            if index >= len(func_list):
                index = len(func_list) - 1

            item = func_list[index]

            if status == 1:
                DisabledFunction.create(
                    function_id=item[0],
                    group_id=data.group_id,
                    status=int(status == 1)
                )
            else:
                DisabledFunction.delete().where(DisabledFunction.function_id == item[0],
                                                DisabledFunction.group_id == data.group_id).execute()

            text = f'已在本群【{data.group_id}】%s功能：%s' % ('关闭' if status == 1 else '打开', item[1])

            return Chain(data).text(text)


@bot.on_group_message(keywords=['功能'])
async def _(data: Message):
    text = [
        '博士，这是阿米娅的功能指引',
        'https://www.amiyabot.com/blog/function.html',
        '如需获得更多帮助，请访问官方网站',
        'https://www.amiyabot.com',
        '或加入官方交流群 362165038',
    ]
    return Chain(data).text('\n'.join(text), auto_convert=False)


@bot.on_group_message(keywords=['代码', '源码'])
async def _(data: Message):
    return Chain(data).text('https://github.com/AmiyaBot/Amiya-Bot')


@bot.on_group_message(keywords=bot.equal('占用'))
async def _(data: Message):
    self = psutil.Process(os.getpid())
    info = self.memory_full_info()

    return Chain(data).text(f'内存占用：{int(info.uss / 1024 / 1024)}mb')
