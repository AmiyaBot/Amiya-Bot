import time

from typing import List
from core import bot, Message, Chain
from core.util import TimeRecorder, any_match, get_index_from_text
from core.database.bot import FunctionUsed, DisabledFunction
from core.database.group import GroupActive, check_group_active

from .about import get_doc


@bot.before_bot_reply
async def _(data: Message, factory_name: str):
    disabled = DisabledFunction.get_or_none(
        function_id=factory_name,
        channel_id=data.channel_id
    )
    if disabled:
        return False

    if not check_group_active(data.channel_id):
        return data.is_admin and bool(any_match(data.text, ['工作', '上班']))

    return True


@bot.after_bot_reply
async def _(data: Chain, factory_name: str):
    _, is_created = FunctionUsed.get_or_create(function_id=factory_name)
    if not is_created:
        FunctionUsed.update(use_num=FunctionUsed.use_num + 1).where(FunctionUsed.function_id == factory_name).execute()


@bot.on_message(keywords='开启功能', level=5)
async def _(data: Message):
    if not data.is_admin:
        return None

    disabled: List[DisabledFunction] = DisabledFunction.select().where(DisabledFunction.channel_id == data.channel_id)

    func_ids = set(bot.plugins.keys()) & set([n.function_id for n in disabled])

    if func_ids:
        content = '有以下可开启的功能：\n\n'
        index = 1
        funcs = []
        for n in func_ids:
            item = bot.plugins[n]
            funcs.append(item)
            content += f'[{index}]{item.name}\n'
            index += 1

        content += '\n回复【序号】开启对应功能'

        reply = await data.wait(Chain(data).text(content))
        if reply:
            index = get_index_from_text(reply.text_digits, funcs)
            if index is not None:
                func = funcs[index]

                DisabledFunction.delete().where(DisabledFunction.channel_id == data.channel_id,
                                                DisabledFunction.function_id == func.plugin_id).execute()

                return Chain(data).text(f'已开启功能【{func.name}】').markdown(get_doc(func))
    else:
        return Chain(data).text('未关闭任何功能，无需开启~')


@bot.on_message(keywords='关闭功能', level=5)
async def _(data: Message):
    if not data.is_admin:
        return None

    disabled: List[DisabledFunction] = DisabledFunction.select().where(DisabledFunction.channel_id == data.channel_id)

    func_ids = set(bot.plugins.keys()) - set([n.function_id for n in disabled])

    if func_ids:
        content = '有以下可关闭的功能：\n\n'
        index = 1
        funcs = []
        for n in func_ids:
            item = bot.plugins[n]
            funcs.append(item)
            content += f'[{index}]{item.name}\n'
            index += 1

        content += '\n回复【序号】关闭对应功能'

        reply = await data.wait(Chain(data).text(content))
        if reply:
            index = get_index_from_text(reply.text_digits, funcs)
            if index is not None:
                func = funcs[index]

                DisabledFunction.create(
                    function_id=func.plugin_id,
                    channel_id=data.channel_id,
                )

                return Chain(data).text(f'已关闭功能【{func.name}】')
    else:
        return Chain(data).text('已经没有可以关闭的功能了~')


@bot.on_message(keywords=['工作', '上班'])
async def _(data: Message):
    if not data.is_admin:
        return None

    group_active: GroupActive = GroupActive.get_or_create(group_id=data.channel_id)[0]

    if group_active.active == 0:
        seconds = int(time.time()) - int(group_active.sleep_time)
        total = TimeRecorder.calc_time_total(seconds)
        text = '打卡上班啦~阿米娅%s休息了%s……' % ('才' if seconds < 600 else '一共', total)
        if seconds < 21600:
            text += '\n博士真是太过分了！哼~ >.<'
        else:
            text += '\n充足的休息才能更好的工作，博士，不要忘记休息哦 ^_^'

        GroupActive.update(active=1, sleep_time=0).where(GroupActive.group_id == data.channel_id).execute()
        return Chain(data).text(text)
    else:
        return Chain(data).text('阿米娅没有偷懒哦博士，请您也不要偷懒~')


@bot.on_message(keywords=['休息', '下班'])
async def _(data: Message):
    if not data.is_admin:
        return None

    group_active: GroupActive = GroupActive.get_or_create(group_id=data.channel_id)[0]

    if group_active.active == 1:
        GroupActive.update(active=0,
                           sleep_time=int(time.time())).where(GroupActive.group_id == data.channel_id).execute()

        return Chain(data).text('打卡下班啦！博士需要的时候再让阿米娅工作吧。^_^')
    else:
        seconds = int(time.time()) - int(group_active.sleep_time)
        total = TimeRecorder.calc_time_total(seconds)
        if 60 < seconds < 21600:
            return Chain(data, at=False).text('（阿米娅似乎已经睡着了...）')
        else:
            if seconds < 60:
                return Chain(data).text('阿米娅已经下班啦，博士需要的时候请让阿米娅工作吧^_^')
            else:
                return Chain(data).text(f'阿米娅已经休息了{total}啦，博士需要的时候请让阿米娅工作吧\n^_^')
