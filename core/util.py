import re
import os
import sys
import time
import yaml
import jieba
import jionlp
import shutil
import string
import random
import difflib
import asyncio
import datetime
import pypinyin

from yaml import SafeDumper
from typing import List
from string import punctuation
from attrdict import AttrDict
from functools import partial
from zhon.hanzi import punctuation as punctuation_cn
from concurrent.futures import ThreadPoolExecutor

jieba.setLogLevel(jieba.logging.INFO)

yaml_cache = {
    'attr': {},
    'dict': {}
}
executor = ThreadPoolExecutor(min(32, (os.cpu_count() or 1) + 4))


async def run_in_thread_pool(block_func, *args, **kwargs):
    """
    使用线程池运行IO阻塞型函数，使其可被等待并切换执行权

    def func(index):
        time.sleep(index)
        return 'Done'

    async def run():
        res = await run_in_thread_pool(func, index)

    :param block_func: IO阻塞型函数
    :param args:       元组参数
    :param kwargs:     字典参数
    :return:
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, partial(block_func, *args, **kwargs))


class TimeRecorder:
    def __init__(self):
        self.time = time.time()

    def rec(self, millisecond=False):
        """
        获取从开始计时到调用时经过了多少秒/毫秒
        :param millisecond: 是否适用毫秒计时
        :return: 单位为秒/毫秒的时间
        """
        mil = 1000 if millisecond else 1
        return int(time.time() * mil - self.time * mil)

    def total(self):
        return self.calc_time_total(self.rec())

    @staticmethod
    def calc_time_total(seconds):
        """
        将秒数转化为日常计时
        :param seconds: 秒数
        :return: 日常计时
        """
        # 将秒数转化为日常计时中 天数+小时+分钟+秒 的形式
        timedelta = datetime.timedelta(seconds=seconds)
        # 获取天数
        day = timedelta.days
        # 获取 时、分、秒
        hour, mint, sec = tuple([
            int(n) for n in str(timedelta).split(',')[-1].split(':')
        ])
        # 转化成汉语字符串
        total = ''
        if day:
            total += '%d天' % day
        if hour:
            total += '%d小时' % hour
        if mint:
            total += '%d分钟' % mint
        # 如果时间超过一分钟，则不显示秒数
        if sec and not (day or hour or mint):
            total += '%d秒' % sec

        return total


# 使用metaclass实现单例类
class Singleton(type):
    instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.instances:
            cls.instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instances[cls]


def argv(name, formatter=str):
    key = f'--{name}'
    if key in sys.argv:
        index = sys.argv.index(key) + 1

        if index >= len(sys.argv):
            return True

        if sys.argv[index].startswith('--'):
            return True
        else:
            return formatter(sys.argv[index])


# 变成按照一定规则将data的key值排序后的有序字典
def sorted_dict(data: dict, *args, **kwargs):
    return {n: data[n] for n in sorted(data, *args, **kwargs)}


def all_match(text: str, items: list):
    """
    判断text中是否包含items中的所有元素
    :param text: 源文本
    :param items: 待匹配元素列表
    :return: 是否匹配
    """
    for item in items:
        if item not in text:
            return False
    return True


def any_match(text: str, items: list):
    """
    判断text中是否包含items中的任一元素
    :param text: 源文本
    :param items: 待匹配元素列表
    :return: 是否匹配
    """
    for item in items:
        if item in text:
            return True
    return False


# 在元素列表中随机选出其中一个
def random_pop(items: list):
    return items.pop(random.randrange(0, len(items)))


def check_sentence_by_re(sentence: str, words: list, names: list):
    """
    按照words的正则表达式在sentence中匹配names中的任一元素
    :param sentence: 待匹配文本
    :param words: 正则列表
    :param names: 填充列表
    :return: 是否匹配
    """
    for item in words:
        for n in names:
            if re.search(re.compile(item % n if '%s' in item else item), sentence):
                return True
    return False


def find_similar_list(text: str, text_list: list, _random: bool = False):
    """
    在text_list中找到和text最接近的字符串
    :param text: 参考字符串
    :param text_list: 待选字符串列表
    :param _random: 若为True，如果有多个字符串与text的相似程度相同，则返回其中任意一个，若为False，则返回所有最接近的字符串
    :return: 最接近的字符串/字符串列表
    """
    result = {}
    for item in text_list:
        rate = float(
            difflib.SequenceMatcher(None, text, item).quick_ratio() * len([n for n in text if n in set(item)])
        )
        if rate > 0:
            if rate not in result:
                result[rate] = []
            result[rate].append(item)

    if not result:
        return None, 0

    high = sorted(result.keys())[-1]
    result = result[high]

    if _random:
        return random.choice(result), high

    return result, high


def read_yaml(path: str, _dict: bool = False, _refresh=True):
    """
    读取yaml配置文件
    :param path: 文件路径
    :param _dict: 若为True，返回一个dict，否则返回AttrDict
    :param _refresh: 若为True或该文件没有被缓存，则从文件中读取，否则从缓存中读取
    :return: dict/AttrDict形式的配置
    """
    t = 'dict' if _dict else 'attr'

    if path in yaml_cache[t] and not _refresh:
        return yaml_cache[t][path]

    with open(path, mode='r', encoding='utf-8') as f:
        content = yaml.safe_load(f)
        if not _dict:
            content = AttrDict(content)

        yaml_cache[t][path] = content

    return content


def create_yaml(path: str, data: dict, overwrite: bool = False):
    """
    根据data创建yaml配置文件
    :param path: 文件路径
    :param data: 配置数据
    :param overwrite: 是否在该path所指向的文件存在时重写yaml
    :return: 是否成功创建
    """
    SafeDumper.add_representer(
        type(None),
        lambda dumper, value: dumper.represent_scalar(u'tag:yaml.org,2002:null', '')
    )
    create_dir(path, is_file=True)

    if os.path.exists(path) and not overwrite:
        return False

    with open(path, mode='w+', encoding='utf-8') as file:
        yaml.safe_dump(data, file, indent=4, default_flow_style=False, allow_unicode=True)

    return True


def create_dir(path: str, is_file: bool = False):
    """
    创建文件/目录
    :param path: 文件/目录路径
    :param is_file: 该path是否为文件
    :return: 标准的文件/目录路径
    """
    if is_file:
        path = '/'.join(path.replace('\\', '/').split('/')[:-1])

    if path and not os.path.exists(path):
        os.makedirs(path)

    return path


def combine_dict(origin: dict, default: dict):
    for key in default.keys():
        if key not in origin:
            origin[key] = default[key]
        else:
            if type(default[key]) is dict:
                combine_dict(origin[key], default[key])
            elif default[key] is not None and not isinstance(origin[key], type(default[key])):
                origin[key] = default[key]

    return origin


def cut_by_jieba(text):
    return jieba.lcut(
        text.lower().replace(' ', '')
    )


def cut_code(code, length):
    code_list = re.findall('.{' + str(length) + '}', code)
    code_list.append(code[(len(code_list) * length):])
    res_list = []
    for n in code_list:
        if n != '':
            res_list.append(n)
    return res_list


def char_seat(char):
    return 0.58 if 32 <= ord(char) <= 126 else 1


def text_to_pinyin(text: str):
    return ''.join([item[0] for item in pypinyin.pinyin(text, style=pypinyin.NORMAL)]).lower()


def remove_dir(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)
    return path


def remove_punctuation(text: str):
    for i in punctuation:
        text = text.replace(i, '')
    for i in punctuation_cn:
        text = text.replace(i, '')
    return text


def remove_xml_tag(text: str):
    return re.compile(r'<[^>]+>', re.S).sub('', text)


def insert_empty(text, max_num, half=False):
    return '%s%s' % (text, ('　' if half else ' ') * (max_num - len(str(text))))


def pascal_case_to_snake_case(camel_case: str):
    snake_case = re.sub(r'(?P<key>[A-Z])', r'_\g<key>', camel_case)
    return snake_case.lower().strip('_')


def snake_case_to_pascal_case(snake_case: str):
    words = snake_case.split('_')
    return ''.join(word.title() if i > 0 else word.lower() for i, word in enumerate(words))


def integer(value):
    if type(value) is float and int(value) == value:
        value = int(value)
    return value


def random_code(length):
    pool = string.digits + string.ascii_letters
    code = ''
    for i in range(length):
        code += random.choice(pool)
    return code


def extract_time(text: str, to_time_point: bool = True):
    result = jionlp.ner.extract_time(text)
    if result:
        try:
            detail = result[0]['detail']

            if detail['type'] in ['time_span', 'time_point']:
                return [time.strptime(n, '%Y-%m-%d %H:%M:%S') for n in detail['time'] if n != 'inf']

            elif detail['type'] == 'time_delta':
                time_length = {
                    'year': 31536000,
                    'month': 2628000,
                    'day': 86400,
                    'hour': 3600,
                    'minute': 60,
                    'second': 1
                }
                time_result = 0
                for k, v in time_length.items():
                    if k in detail['time']:
                        if to_time_point:
                            return [time.localtime(time.time() + detail['time'][k] * v)]
                        time_result += detail['time'][k] * v
                return time_result

            elif detail['type'] == 'time_period':
                pass

        except OSError:
            pass
    return []


def chinese_to_digits(text: str):
    character_relation = {
        '零': 0,
        '一': 1,
        '二': 2,
        '两': 2,
        '三': 3,
        '四': 4,
        '五': 5,
        '六': 6,
        '七': 7,
        '八': 8,
        '九': 9,
        '十': 10,
        '百': 100,
        '千': 1000,
        '万': 10000,
        '亿': 100000000
    }
    start_symbol = ['一', '二', '两', '三', '四', '五', '六', '七', '八', '九', '十']
    more_symbol = list(character_relation.keys())

    symbol_str = ''
    found = False

    def _digits(chinese: str):
        total = 0
        r = 1
        for i in range(len(chinese) - 1, -1, -1):
            val = character_relation[chinese[i]]
            if val >= 10 and i == 0:
                if val > r:
                    r = val
                    total = total + val
                else:
                    r = r * val
            elif val >= 10:
                if val > r:
                    r = val
                else:
                    r = r * val
            else:
                total = total + r * val
        return total

    for item in text:
        if item in start_symbol:
            if not found:
                found = True
            symbol_str += item
        else:
            if found:
                if item in more_symbol:
                    symbol_str += item
                    continue
                else:
                    digits = str(_digits(symbol_str))
                    text = text.replace(symbol_str, digits, 1)
                    symbol_str = ''
                    found = False

    if symbol_str:
        digits = str(_digits(symbol_str))
        text = text.replace(symbol_str, digits, 1)

    return text


def is_all_chinese(text: List[str]):
    """
    判断列表中所有的字符串是否全部为汉字
    :param text: 字符串列表
    :return: 是否全为汉字
    """
    for word in text:
        for char in word:
            if not '\u4e00' <= char <= '\u9fff':
                return False
    return True


def number_with_sign(number: int):
    if number >= 0:
        return '+' + str(number)
    return str(number)
