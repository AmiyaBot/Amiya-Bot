import time

from typing import Union
from core import bot, websocket, http, Message, Chain, Mirai
from core.util import TimeRecorder
from core.database.group import Group, GroupActive
from core.control import StateControl
from core.config import config


@bot.on_group_message(function_id='admin', keywords=['休息', '下班'])
async def _(data: Message):
    if not data.is_admin and not data.is_group_admin:
        return None

    group_active: GroupActive = GroupActive.get_or_create(group_id=data.group_id)[0]

    if group_active.active == 1:
        GroupActive.update(active=0,
                           sleep_time=int(time.time())).where(GroupActive.group_id == data.group_id).execute()

        return Chain(data).text('打卡下班啦！博士需要的时候再让阿米娅工作吧。^_^')
    else:
        seconds = int(time.time()) - int(group_active.sleep_time)
        total = TimeRecorder.calc_time_total(seconds)

        return Chain(data).text(f'阿米娅休息了{total}，博士需要的时候请让阿米娅工作吧。^_^')


@bot.on_group_message(function_id='admin', keywords=['工作', '上班'])
async def _(data: Message):
    if not data.is_admin and not data.is_group_admin:
        return None

    group_active: GroupActive = GroupActive.get_or_create(group_id=data.group_id)[0]

    if group_active.active == 0:
        seconds = int(time.time()) - int(group_active.sleep_time)
        total = TimeRecorder.calc_time_total(seconds)
        text = '打卡上班啦~阿米娅%s休息了%s……' % ('才' if seconds < 600 else '一共', total)
        if seconds < 600:
            text += '\n博士真是太过分了！哼~ >.<'
        else:
            text += '\n充足的休息才能更好的工作，博士，不要忘记休息哦 ^_^'

        GroupActive.update(active=1, sleep_time=0).where(GroupActive.group_id == data.group_id).execute()
        return Chain(data).text(text)
    else:
        return Chain(data).text('阿米娅没有偷懒哦博士，请您也不要偷懒~')


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
        Group.insert_data(group_list)
        await data.send(Chain(data).text(f'同步完成，共 {len(group_list)} 个群。'))


@bot.on_event(Mirai.BotInvitedJoinGroupRequestEvent)
async def _(event: Mirai.BotInvitedJoinGroupRequestEvent):
    if event.fromId in config.admin.accounts:
        await event.handle(allow=True, message='同意邀请')
    else:
        await event.handle(allow=False, message='仅允许管理员邀请')


@bot.on_event([Mirai.BotMuteEvent, Mirai.BotLeaveEventKick, Mirai.BotLeaveEventActive])
async def _(data: Union[Mirai.BotMuteEvent, Mirai.BotLeaveEventKick, Mirai.BotLeaveEventActive]):
    flag = False
    if type(data) is Mirai.BotMuteEvent:
        group_id = data.operator.group.id
        flag = True
    else:
        group_id = data.group.id

    await http.leave_group(group_id, flag)
    async with websocket.send_to_admin() as chain:
        chain.text(f'已退出群{group_id}，原因：{data}')


@bot.on_overspeed
async def _(data: Message):
    return Chain(data).text('博士说话太快了，请再慢一些吧~')
