import time

from core.util.config import func_setting


def calc_jade(end_date):
    dates = calc_date(end_date)

    conf = func_setting().jadeSetting
    sign_in = conf.signIn
    daily_tasks = conf.dailyTasks
    weekly_tasks = conf.weeklyTasks
    weekly_battle = conf.weeklyBattle

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

    result = '（阿米娅计算着罗德岛的物资流水...）\n博士，不含制造站，罗德岛可在 %s 前\n预计得到 %d 合成玉\n\n' % (end_date, jade)

    result += '月卡签到共计：%d\n' % types['s']
    result += '每日任务共计：%d\n' % types['d']
    result += '每周任务共计：%d\n' % types['t']
    result += '剿灭行动共计：%d\n' % types['b']

    result += '\n博士，要好好规划罗德岛的资源使用哦～'

    return result


def calc_date(end_date):
    time_str = stamp_to_date(int(time.time()))

    now_time = date_to_stamp(time_str)
    end_time = date_to_stamp(end_date)

    dates = []

    while now_time < end_time:
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
