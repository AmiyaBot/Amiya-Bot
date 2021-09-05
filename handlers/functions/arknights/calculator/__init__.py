import re
import time

from core import Message, Chain
from dataSource import DataSource
from handlers.constraint import FuncInterface

from .calculator import calc_jade

re_list = [
    '(\\d+)年(\\d+)月(\\d+)日.*玉',
    '(\\d+)年(\\d+)月(\\d+)号.*玉',
    '(\\d+)-(\\d+)-(\\d+).*玉',
    '(\\d+)/(\\d+)/(\\d+).*玉',
    '(\\d+)月(\\d+)日.*玉',
    '(\\d+)月(\\d+)号.*玉',
    '(\\d+)-(\\d+).*玉',
    '(\\d+)/(\\d+).*玉'
]


class Calculator(FuncInterface):
    def __init__(self, data_source: DataSource):
        super().__init__(function_id='jadeCalculator')

        self.data = data_source

    @FuncInterface.is_disable
    def check(self, data: Message):
        for item in re_list:
            r = re.search(re.compile(item), data.text_digits)
            if r:
                return True
        return False

    @FuncInterface.is_used
    def action(self, data: Message):

        reply = Chain(data)

        for item in re_list:
            r = re.search(re.compile(item), data.text_digits)
            if r:
                length = item.count('\\d+')
                if length == 2:
                    date = [str(time.localtime().tm_year), r.group(1), r.group(2)]
                else:
                    date = [r.group(1), r.group(2), r.group(3)]
                date = '-'.join(date)

                try:
                    time_array = time.strptime(date, '%Y-%m-%d')
                    time_stamp = time.mktime(time_array)
                except ValueError:
                    return reply.text('博士，这个日期真的没问题吗？')
                except OverflowError:
                    return reply.text('博士，阿米娅算不过来了… >.<')

                if time.time() >= time_stamp:
                    return reply.text('博士，过去的只能成为了过去，我们只需要朝着我们的未来前进就好，可以的话，阿米娅会一直陪在博士身边的[face21]')

                text = calc_jade(date)
                return reply.text(text)
