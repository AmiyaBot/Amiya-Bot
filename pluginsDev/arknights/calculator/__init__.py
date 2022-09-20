import re
import time

from amiyabot import PluginInstance
from core import Message, Chain
from core.util import extract_time

sign_in = 200
daily_tasks = 100
weekly_tasks = 500
weekly_battle = 1800

bot = PluginInstance(
    name='明日方舟合成玉计算',
    version='1.0',
    plugin_id='amiyabot-arknights-jade'
)


def calc_jade(end_date):
    dates = calc_date(end_date)
    end_date_str = stamp_to_date(end_date)

    types = {'s': 0, 'd': 0, 't': 0, 'b': 0}

    for item in dates:
        types['s'] += sign_in
        types['d'] += daily_tasks
        if item['weekDate'] == 0:
            types['t'] += weekly_tasks
            types['b'] += weekly_battle

    jade = 0
    for i in types:
        jade += types[i]

    result = f'（阿米娅计算着罗德岛的物资流水...）\n\n博士，不含制造站，罗德岛可在 {end_date_str} 前\n预计得到 {jade} 合成玉\n\n'

    result += '月卡签到共计：%d\n' % types['s']
    result += '每日任务共计：%d\n' % types['d']
    result += '每周任务共计：%d\n' % types['t']
    result += '剿灭行动共计：%d\n' % types['b']

    result += '\n博士，要好好规划罗德岛的资源使用哦～'

    return result


def calc_date(end_date):
    now_time = date_to_stamp(stamp_to_date(int(time.time())))

    dates = []

    while now_time < end_date:
        now_time += 86400
        time_array = time.localtime(now_time)
        dates.append({
            'dateStr': stamp_to_date(now_time),
            'weekDate': time_array.tm_wday
        })

    return dates


def date_to_stamp(date):
    time_stamp = time.strptime(date, '%Y-%m-%d')
    return int(time.mktime(time_stamp))


def stamp_to_date(stamp):
    time_array = time.localtime(stamp)
    return time.strftime('%Y-%m-%d', time_array)


async def verify(data: Message):
    return bool(re.search(r'多少(合成)?玉', data.text)), 3


async def calc_result(reply: Chain, text: str):
    try:
        time_array = extract_time(text)
        if time_array:
            time_array = time_array[-1]

            year = time.localtime().tm_year

            if time_array.tm_year - year > 100:
                return reply.text('博士，这片大地变幻莫测，罗德岛的未来有太多不可预期，阿米娅觉得我们更应该把眼光放在当下[face:21]')

            time_stamp = time.mktime(time_array)
            if time.time() >= time_stamp:
                return reply.text('博士，过去的只能成为了过去，我们只需要朝着我们的未来前进就好，可以的话，阿米娅会一直陪在博士身边的[face:21]')

            text = calc_jade(time_stamp)

            return reply.text(text)

    except ValueError:
        return reply.text('博士，这个日期真的没问题吗？')
    except OverflowError:
        return reply.text('博士，阿米娅算不过来了… >.<')


@bot.on_message(keywords=['/计算合成玉'], level=3)
async def action(data: Message):
    wait = await data.wait(Chain(data).text('博士，请说明需要计算从今天起的合成玉的截止日期，可以为时间、日期或节日'))
    if not wait or not wait.text:
        return None

    return await calc_result(Chain(wait), wait.text_origin)


@bot.on_message(verify=verify, allow_direct=True)
async def action(data: Message):
    reply = Chain(data)

    return await calc_result(reply, data.text_origin)
