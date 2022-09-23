import time
import asyncio

from amiyabot import PluginInstance

from core.database.group import GroupSetting
from core.database.messages import *
from core.util import TimeRecorder
from core import send_to_console_channel, tasks_control, Message, Chain, SourceServer, TencentBotInstance, \
    bot as main_bot

from helper import WeiboUser, weibo_conf, weibo_plugin

bot = PluginInstance(
    name='微博自动推送',
    version='1.1',
    plugin_id='amiyabot-weibo',
    plugin_type='official',
    description='可在微博更新时自动推送到群/频道',
    document=f'{weibo_plugin}/README.md'
)


@table
class WeiboRecord(MessageBaseModel):
    user_id: int = IntegerField()
    blog_id: str = CharField()
    record_time: int = IntegerField()


async def send_by_index(index: int, weibo: WeiboUser, data: Message):
    result = await weibo.get_weibo_content(index - 1)

    if not result:
        return Chain(data).text('博士…暂时无法获取微博呢…请稍后再试吧')
    else:
        return Chain(data) \
            .text(result.user_name + '\n') \
            .text(result.html_text + '\n') \
            .image(result.pics_list)


@bot.on_message(group_id='weibo', keywords=['开启微博推送'])
async def _(data: Message):
    if not data.is_admin:
        return Chain(data).text('抱歉，微博推送只能由管理员设置')

    channel: GroupSetting = GroupSetting.get_or_none(group_id=data.channel_id, bot_id=data.instance.appid)
    if channel:
        GroupSetting.update(send_weibo=1).where(GroupSetting.group_id == data.channel_id,
                                                GroupSetting.bot_id == data.instance.appid).execute()
    else:
        GroupSetting.create(group_id=data.channel_id,
                            bot_id=data.instance.appid,
                            send_weibo=1)

    return Chain(data).text('已在本频道开启微博推送')


@bot.on_message(group_id='weibo', keywords=['关闭微博推送'])
async def _(data: Message):
    if not data.is_admin:
        return Chain(data).text('抱歉，微博推送只能由管理员设置')

    GroupSetting.update(send_weibo=0).where(GroupSetting.group_id == data.channel_id,
                                            GroupSetting.bot_id == data.instance.appid).execute()

    return Chain(data).text('已在本频道关闭微博推送')


@bot.on_message(group_id='weibo', keywords=['微博'])
async def _(data: Message):
    message = data.text_digits
    index = 0

    r = re.search(r'(\d+)', message)
    if r:
        index = abs(int(r.group(1)))

    if '最新' in message:
        index = 1

    weibo = WeiboUser(weibo_conf.listen[0])

    if index:
        return await send_by_index(index, weibo, data)
    else:
        result = await weibo.get_blog_list()
        user_name = await weibo.get_user_name()
        if not result:
            return Chain(data).text('博士…暂时无法获取微博列表呢…请稍后再试吧')

        reply = Chain(data) \
            .text(f'这是 {user_name} 的微博列表') \
            .text_image(result) \
            .text('回复【序号】或和我说「阿米娅第 N 条微博」来获取详情吧')

        wait = await data.wait(reply)
        if wait:
            r = re.search(r'(\d+)', wait.text_digits)
            if r:
                index = abs(int(r.group(1)))
                return await send_by_index(index, weibo, wait)


@tasks_control.timed_task(each=30)
async def _():
    for user in weibo_conf.listen:
        weibo = WeiboUser(user)
        new_id = await weibo.get_weibo_id(0)
        if not new_id:
            continue

        record = WeiboRecord.get_or_none(blog_id=new_id)
        if record:
            continue

        WeiboRecord.create(
            user_id=user,
            blog_id=new_id,
            record_time=int(time.time())
        )

        target: List[GroupSetting] = GroupSetting.select().where(GroupSetting.send_weibo == 1)

        time_rec = TimeRecorder()
        result = await weibo.get_weibo_content(0)

        if not result:
            await send_to_console_channel(Chain().text(f'微博获取失败\nUSER: {user}\nID: {new_id}'))
            return

        await send_to_console_channel(
            Chain().text(f'开始推送微博\nUSER: {result.user_name}\nID: {new_id}\n目标数: {len(target)}')
        )

        for item in target:
            data = Chain()

            instance = main_bot[item.bot_id]

            if not instance:
                continue

            if type(instance.instance) is TencentBotInstance:
                data.builder = SourceServer()

            data.text(f'来自 {result.user_name} 的最新微博\n\n{result.html_text}')
            data.image(result.pics_list)

            await instance.send_message(data, channel_id=item.group_id)
            await asyncio.sleep(0.2)

        await send_to_console_channel(Chain().text(f'微博推送结束:\n{new_id}\n耗时{time_rec.total()}'))
