import re

from core import log, bot, Message, Chain

from .gacha import GachaForUser, UserGachaInfo

re_list = [
    r'抽卡\d+次',
    r'寻访\d+次',
    r'抽\d+次',
    r'\d+次寻访',
    r'\d+连寻访',
    r'\d+连抽',
    r'\d+连',
    r'\d+抽'
]


def find_once(reg, text):
    r = re.compile(reg)
    f = r.findall(text)
    if len(f):
        return f[0]
    return ''


@bot.on_group_message(function_id='gacha', keywords=['抽', '连', '寻访'])
async def _(data: Message):
    try:
        gc = GachaForUser(data)
    except Exception as e:
        log.error(e)
        return Chain(data).text('无法初始化卡池')

    coupon = gc.user_gacha.coupon
    message = data.text_digits

    reply = Chain(data)

    for item in re_list:
        r = re.search(item, message)
        if r:
            times = int(find_once(r'\d+', find_once(item, message)))

            if times <= 0:
                return reply.text('博士在捉弄阿米娅吗 >.<')
            if times > 300:
                return reply.text('博士不要着急，罗德岛的资源要好好规划使用哦，先试试 300 次以内的寻访吧 (#^.^#)')
            if times > coupon:
                return reply.text('博士，您的寻访凭证（%d张）不够哦~' % coupon)

            if times <= 10:
                return gc.detailed_mode(times, ten_times=times == 10)
            else:
                return gc.continuous_mode(times)
