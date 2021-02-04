import re
import time

from modules.commonMethods import Reply
from functions.jadeCalculator.calculator import calc_jade

re_list = [
    "(\\d+)年(\\d+)月(\\d+)日.*玉",
    "(\\d+)年(\\d+)月(\\d+)号.*玉",
    "(\\d+)-(\\d+)-(\\d+).*玉",
    "(\\d+)/(\\d+)/(\\d+).*玉",
    "(\\d+)月(\\d+)日.*玉",
    "(\\d+)月(\\d+)号.*玉",
    "(\\d+)-(\\d+).*玉",
    "(\\d+)/(\\d+).*玉"
]


class Init:
    def __init__(self):
        self.function_id = 'jadeCalculator'
        self.keyword = ['玉']

    @staticmethod
    def action(data):

        message = data['text_digits']

        for item in re_list:
            r = re.search(re.compile(item), message)
            if r:
                length = item.count('\\d+')
                if length == 2:
                    date = ['2021', r.group(1), r.group(2)]
                else:
                    date = [r.group(1), r.group(2), r.group(3)]
                date = '-'.join(date)

                try:
                    time_array = time.strptime(date, '%Y-%m-%d')
                    time_stamp = time.mktime(time_array)
                except ValueError:
                    return Reply('博士，这个日期真的没问题吗？')
                except OverflowError:
                    return Reply('博士，阿米娅算不过来了… >.<')

                if time.time() >= time_stamp:
                    return Reply('博士，过去的只能成为了过去，我们只需要朝着我们的未来前进就好，可以的话，阿米娅会一直陪在博士身边的')

                text = calc_jade(date)
                return Reply(text)
