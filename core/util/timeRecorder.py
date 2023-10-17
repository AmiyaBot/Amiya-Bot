import time
import datetime


class TimeRecorder:
    def __init__(self):
        self.time = time.time()

    def rec(self, millisecond=False):
        mil = 1000 if millisecond else 1
        return int(time.time() * mil - self.time * mil)

    def total(self):
        return self.calc_time_total(self.rec())

    @staticmethod
    def calc_time_total(seconds):
        timedelta = datetime.timedelta(seconds=seconds)
        day = timedelta.days
        hour, mint, sec = tuple([int(n) for n in str(timedelta).split(',')[-1].split(':')])
        total = ''
        if day:
            total += '%d天' % day
        if hour:
            total += '%d小时' % hour
        if mint:
            total += '%d分钟' % mint
        if sec:
            total += '%d秒' % sec

        return total
