import os
import psutil

from core import bot, http, Message, Chain, Mirai
from core.database.group import Group
from core.control import StateControl
from core.config import config


@bot.on_private_message(keywords=bot.equal('重启'))
async def _(data: Message):
    if data.is_admin:
        await data.send(Chain(data).text('准备重启...正在等待所有任务结束...'))
        StateControl.shutdown()


@bot.on_private_message(keywords=bot.equal('同步群'))
async def _(data: Message):
    if data.is_admin:
        group_list = await http.get_group_list()
        Group.truncate_table()
        Group.insert_many(group_list).execute()
        await data.send(Chain(data).text(f'同步完成，共 {len(group_list)} 个群。'))


@bot.on_group_message(keywords=bot.equal('占用'))
async def _(data: Message):
    self = psutil.Process(os.getpid())
    info = self.memory_full_info()

    return Chain(data).text(f'内存占用：{int(info.uss / 1024 / 1024)}mb')


@bot.on_event(Mirai.BotInvitedJoinGroupRequestEvent)
async def _(event: Mirai.BotInvitedJoinGroupRequestEvent):
    if event.fromId in config.admin.accounts:
        await event.handle(allow=True, message='同意邀请')
    else:
        await event.handle(allow=False, message='仅允许管理员邀请')


@bot.on_overspeed
async def _(data: Message):
    return Chain(data).text('博士说话太快了，请再慢一些吧~')
