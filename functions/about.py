import os

from core import bot, Message, Chain
from core.util import get_index_from_text


@bot.on_message(keywords=['功能', '帮助', '说明', 'help'], allow_direct=True)
async def _(data: Message):
    content = "# 功能清单\n\n管理员发送 `兔兔上班/下班` 即可开启或关闭兔兔\n\n回复下列的【序号】，可查询详细的功能描述。\n\n"

    index = 1
    funcs = []
    for _, item in bot.plugins.items():
        funcs.append(item)
        content += f'【{index}】{item.name}<br>'
        index += 1

    reply = await data.wait(Chain(data).markdown(content))
    if reply:
        index = get_index_from_text(reply.text_digits, funcs)
        if index is not None:
            title = funcs[index].name
            doc = funcs[index].document
            if os.path.isfile(doc):
                with open(doc, mode='r', encoding='utf-8') as file:
                    content = file.read()
            else:
                content = doc

            return Chain(reply).markdown(f'# {title}\n\n{content}')


@bot.on_message(keywords=['频道信息'])
async def _(data: Message):
    return Chain(data, at=False).text(
        f'用户ID：{data.user_id}\n'
        f'频道ID：{data.guild_id}\n'
        f'子频道ID：{data.channel_id}'
    )
