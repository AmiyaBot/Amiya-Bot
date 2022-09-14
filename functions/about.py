from core import bot, Message, Chain


@bot.on_message(keywords=['功能', '帮助', '说明', 'help'], allow_direct=True)
async def _(data: Message):
    with open('functions/_docs/function.md', mode='r', encoding='utf-8') as file:
        doc = file.read()
    return Chain(data).html('template/function/function.html', {'doc': doc}, render_time=1000)


@bot.on_message(keywords=['频道信息'])
async def _(data: Message):
    return Chain(data, at=False).text(
        f'用户ID：{data.user_id}\n'
        f'频道ID：{data.guild_id}\n'
        f'子频道ID：{data.channel_id}'
    )
