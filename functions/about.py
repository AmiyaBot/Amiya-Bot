import os
import psutil

from core import bot, Message, Chain


@bot.on_group_message(keywords=['代码', '源码'])
async def _(data: Message):
    return Chain(data).text('https://github.com/AmiyaBot/Amiya-Bot')


@bot.on_group_message(keywords=bot.equal('占用'))
async def _(data: Message):
    self = psutil.Process(os.getpid())
    info = self.memory_full_info()

    return Chain(data).text(f'内存占用：{int(info.uss / 1024 / 1024)}mb')
