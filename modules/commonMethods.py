import os
import re
import sys
import json
import difflib

from message.messageType import TextImage, Image, Text

with open('config.json') as conf:
    config = json.load(conf)


class Reply:
    def __init__(self, content, feeling=2, sign=0, coupon=0, at=True, auto_image=True):

        self.auto_image = auto_image

        c_type = type(content)
        chain = []

        if c_type is str:
            chain += self.__trans_str(content.strip('\n'))
        elif c_type is list:
            for item in content:
                if type(item) is str:
                    chain += self.__trans_str(item.strip('\n'))
                if type(item) in [TextImage, Image, Text]:
                    chain += item.item
        else:
            if c_type in [TextImage, Image, Text]:
                chain += content.item

        self.content = chain
        self.feeling = feeling
        self.coupon = coupon
        self.sign = sign
        self.at = at

    def __trans_str(self, text):
        max_len = config['message']['reply_text_max_length']
        if self.auto_image and len(text) >= max_len:
            text = TextImage(text)
        else:
            text = Text(text)
        return text.item


def list_split(items: list, n: int):
    return [items[i:i + n] for i in range(0, len(items), n)]


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


def find_similar_string(text: str, text_list: list, hard=0.4):
    r = 0
    t = ''
    for item in text_list:
        rate = float(string_equal_rate(text, item))
        if rate > r and rate >= hard:
            r = rate
            t = item
    return t


def string_equal_rate(str1: str, str2: str):
    return difflib.SequenceMatcher(None, str1, str2).quick_ratio()


def restart():
    python = sys.executable
    os.execl(python, python, *sys.argv)
