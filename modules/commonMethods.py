import os
import re
import sys
import difflib
import datetime

from string import punctuation
from zhon.hanzi import punctuation as punctuation_cn
from message.messageType import TextImage, Image, Voice, Text
from modules.config import get_config


class Reply:
    def __init__(self, content, feeling=2, sign=0, coupon=0, at=True, auto_image=True):

        self.config = get_config()
        self.auto_image = auto_image

        c_type = type(content)
        chain = []

        sp = [TextImage, Image, Voice, Text]
        if c_type is str:
            chain += self.__trans_str(content.strip('\n'))
        elif c_type is list:
            for item in content:
                if type(item) is str:
                    chain += self.__trans_str(item.strip('\n'))
                if type(item) in sp:
                    chain += item.item
        else:
            if c_type in sp:
                chain += content.item

        self.content = chain
        self.feeling = feeling
        self.coupon = coupon
        self.sign = sign
        self.at = at

    def __trans_str(self, text):
        max_len = self.config['message']['reply_text_max_length']
        if self.auto_image and len(text) >= max_len:
            text = TextImage(text)
        else:
            text = Text(text)
        return text.item


def word_in_sentence(sentence: str, words: list):
    for word in words:
        if word in sentence:
            return True
    return False


def check_sentence_by_re(sentence: str, words: list, names: list):
    for item in words:
        for n in names:
            if re.search(re.compile(item % n if '%s' in item else item), sentence):
                return True
    return False


def all_item_in_text(text: str, items: list):
    for item in items:
        if item not in text:
            return False
    return True


def insert_empty(text, max_num, half=False):
    return '%s%s' % (text, ('　' if half else ' ') * (max_num - len(str(text))))


def insert_zero(num: int):
    return ('0%d' % num) if num < 10 else str(num)


def find_similar_string(text: str, text_list: list, hard=0.4, return_rate=False):
    r = 0
    t = ''
    for item in text_list:
        rate = float(string_equal_rate(text, item))
        if rate > r and rate >= hard:
            r = rate
            t = item
    return (t, r) if return_rate else t


def string_equal_rate(str1: str, str2: str):
    return difflib.SequenceMatcher(None, str1, str2).quick_ratio()


def calc_time_total(seconds):
    timedelta = datetime.timedelta(seconds=seconds)
    day = timedelta.days
    hour, mint, sec = tuple([
        int(n) for n in str(timedelta).split(',')[-1].split(':')
    ])
    total = ''
    if day:
        total += '%d天' % day
    if hour:
        total += '%d小时' % hour
    if mint:
        total += '%d分钟' % mint
    if sec and not (day or hour or mint):
        total += '%d秒' % sec

    return total


def remove_xml_tag(text: str):
    return re.compile(r'<[^>]+>', re.S).sub('', text)


def remove_punctuation(text: str):
    for i in punctuation:
        text = text.replace(i, '')
    for i in punctuation_cn:
        text = text.replace(i, '')
    return text


def maintain_record(date: str = None):
    rc_path = 'temp/maintainRecord.txt'
    if date:
        with open(rc_path, mode='w+') as rc:
            rc.write(date)
            return True
    if os.path.exists(rc_path):
        with open(rc_path, mode='r+') as rc:
            return int(rc.read())
    return 0


def restart():
    python = sys.executable
    os.execl(python, python, *sys.argv)
