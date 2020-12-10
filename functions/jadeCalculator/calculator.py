import time

SignIn = 200
DailyTasks = 100
WeeklyTasks = 500
WeeklyBattle = 1800


def calc_jade(end_date):
    dates = calc_date(end_date)

    types = {'s': 0, 'd': 0, 't': 0, 'b': 0}

    for item in dates:
        types['s'] += SignIn
        types['d'] += DailyTasks
        if item['weekDate'] == 0:
            types['t'] += WeeklyTasks
            types['b'] += WeeklyBattle

    jade = 0
    for i in types:
        jade += types[i]

    result = '（阿米娅计算着罗德岛的物资流水...）\n博士，不含制造站，罗德岛可在 %s 前\n预计得到 %d 合成玉\n\n' % (end_date, jade)
    result += '可露希尔每日供应共计：%d\n' % types['s']
    result += '值日外勤小组共计可收获：%d\n' % types['d']
    result += '值周外勤小组共计可收获：%d\n' % types['t']
    result += '剿灭行动小组共计可收获：%d\n' % types['b']

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
