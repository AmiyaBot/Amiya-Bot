import os

from typing import List
from amiyabot import PluginInstance
from core.database.bot import DisabledFunction
from core.util import get_index_from_text
from core import bot, Message, Chain


def get_doc(func: PluginInstance):
    doc = func.document
    if os.path.isfile(doc):
        with open(doc, mode='r', encoding='utf-8') as file:
            content = file.read()
    else:
        content = doc

    return f'# {func.name}\n\n{content}'


@bot.on_message(keywords=['功能', '帮助', '说明', 'help'], allow_direct=True)
async def _(data: Message):
    disabled_funcs: List[DisabledFunction] = DisabledFunction.select().where(
        DisabledFunction.channel_id == data.channel_id
    )
    disabled = [n.function_id for n in disabled_funcs]

    content = "功能清单\n\n" \
              "频道/群管理员发送 `兔兔上班/下班` 可开启或关闭兔兔\n" \
              "频道/群管理员发送 `兔兔开启功能/关闭功能` 可开关单个功能\n\n"

    index = 1
    funcs = []
    for _, item in bot.plugins.items():
        funcs.append(item)
        content += f'[{index}]{item.name}%s\n' % ('（已关闭）' if item.plugin_id in disabled else '')
        index += 1

    content += '\n回复【序号】查询详细的功能描述'

    reply = await data.wait(Chain(data).text(content))
    if reply:
        index = get_index_from_text(reply.text_digits, funcs)
        if index is not None:
            return Chain(reply).markdown(get_doc(funcs[index]))


@bot.on_message(keywords=['频道信息'])
async def _(data: Message):
    return Chain(data, at=False).text(
        f'用户ID：{data.user_id}\n'
        f'频道ID：{data.guild_id}\n'
        f'子频道ID：{data.channel_id}'
    )
