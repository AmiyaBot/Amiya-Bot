import re

from typing import List
from core.util import any_match
from core import log, bot, Message, Chain
from core.database.user import UserInfo, UserGachaInfo
from core.database.bot import Pool

from .gacha import GachaForUser
from .box import get_user_box

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


def change_pool(item: Pool, user_id=None):
    task = UserGachaInfo.update(gacha_pool=item.id).where(
        (UserGachaInfo.user_id == user_id) if user_id else None
    )
    task.execute()

    text = [
        f'{"所有" if not user_id else ""}博士的卡池已切换为{"【限定】" if item.limit_pool != 0 else ""}【{item.pool_name}】\n'
    ]
    if item.pickup_6:
        text.append('[[cl ★★★★★★@#FF4343 cle]] %s' % item.pickup_6.replace(',', '、'))
    if item.pickup_5:
        text.append('[[cl ★★★★★@#FEA63A cle]　] %s' % item.pickup_5.replace(',', '、'))
    if item.pickup_4:
        text.append('[[cl ☆☆☆☆@#A288B5 cle]　　] %s' % item.pickup_4.replace(',', '、'))

    return '\n'.join(text)


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

    times = 0

    for item in re_list:

        r = re.search(item, message)
        if r:
            times = int(find_once(r'\d+', find_once(item, message)))

    if not times:
        if '单抽' in data.text:
            times = 1

    if times:
        user_info: UserInfo = UserInfo.get_user(data.user_id)

        coupon_need = times
        point_need = 0

        if times > 300:
            return reply.text('博士不要着急，罗德岛的资源要好好规划使用哦，先试试 300 次以内的寻访吧 (#^.^#)')
        if times > coupon:
            coupon_need = coupon
            point_need = (times - coupon) * 600

            if user_info.jade_point >= point_need:
                await data.send(Chain(data).text(f'寻访凭证剩余{coupon}张，将消耗{point_need}合成玉'))
            else:
                return reply.text(f'博士，您的寻访资源不够哦~\n寻访凭证剩余{coupon}张\n合成玉剩余{user_info.jade_point}')

        if times <= 10:
            return gc.detailed_mode(times, coupon_need, point_need, ten_times=times == 10)
        else:
            return gc.continuous_mode(times, coupon_need, point_need)

    if any_match(message, ['多少', '几']):
        text = '博士的寻访凭证还剩余 %d 张~' % coupon
        if coupon:
            text += '\n博士，快去获得您想要的干员吧 ☆_☆'
        return reply.text(text)


@bot.on_group_message(function_id='gacha', keywords=['保底'])
async def _(data: Message):
    user: UserGachaInfo = UserGachaInfo.get_or_create(user_id=data.user_id)[0]

    break_even_rate = 98
    if user.gacha_break_even > 50:
        break_even_rate -= (user.gacha_break_even - 50) * 2

    return Chain(data).text(
        f'当前已经抽取了 {user.gacha_break_even} 次而未获得六星干员\n下次抽出六星干员的概率为 {100 - break_even_rate}%'
    )


@bot.on_group_message(function_id='gacha', keywords=['卡池', '池子'])
async def _(data: Message):
    all_pools: List[Pool] = Pool.select()

    message = data.text

    if any_match(message, ['切换', '更换']):

        all_people = data.is_admin and '所有人' in message

        r = re.search(r'(\d+)', data.text_digits)
        if r:
            index = int(r.group(1)) - 1
            if 0 <= index < len(all_pools):
                message = all_pools[index].pool_name

        for item in all_pools:
            if item.pool_name in message:
                return Chain(data).text_image(change_pool(item, data.user_id if not all_people else None))

    text = '博士，这是可更换的卡池列表：\n\n'
    pools = []
    max_len = 0
    for index, item in enumerate(all_pools):
        pool = '%s [ %s ]' % (('' if index + 1 >= 10 else '0') + str(index + 1), item.pool_name)
        if index % 2 == 0 and len(pool) > max_len:
            max_len = len(pool)
        pools.append(pool)

    pools_table = ''
    curr_row = 0
    for index, item in enumerate(pools):
        if index % 2 == 0:
            pools_table += item
            curr_row = len(item)
        else:
            spaces = max_len - curr_row + 2
            pools_table += '%s%s\n' % ('　' * spaces, item)
            curr_row = 0

    if curr_row != 0:
        pools_table += '\n'

    text += pools_table

    wait = await data.waiting(
        Chain(data).text_image(text).text('要切换卡池，请回复【序号】或和阿米娅说「阿米娅切换卡池 "卡池名称" 」\n或「阿米娅切换第 N 个卡池」')
    )
    if wait:
        r = re.search(r'(\d+)', wait.text_digits)
        if r:
            index = int(r.group(1)) - 1
            if 0 <= index < len(all_pools):
                return Chain(data).text_image(change_pool(all_pools[index], data.user_id))
            else:
                return Chain(data).text('博士，要告诉阿米娅准确的卡池序号哦')


@bot.on_group_message(function_id='gacha', keywords=['box'])
async def _(data: Message):
    res = get_user_box(data.user_id)

    if type(res) is str:
        return Chain(data).text(res)

    return Chain(data).image(res)
