from core import bot, Message, Chain


@bot.on_message(keywords=['功能', '帮助', '说明', 'help'], allow_direct=True)
async def _(data: Message):
    return Chain(data).html('template/function/function.html', render_time=1000)


@bot.on_message(keywords=['频道信息'])
async def _(data: Message):
    return Chain(data, at=False).text(f'频道ID：{data.guild_id}\n子频道ID：{data.channel_id}')
