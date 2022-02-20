import re
import os
import time
import yaml
import jieba
import jionlp
import string
import random
import difflib
import asyncio
import datetime
import pypinyin

from yaml import SafeDumper
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
    :param args:       元祖参数
    :param kwargs:     字典参数
    :return:
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, partial(block_func, *args, **kwargs))


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


class Singleton(type):
    instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.instances:
            cls.instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instances[cls]


def sorted_dict(data: dict, *args, **kwargs):
    return {n: data[n] for n in sorted(data, *args, **kwargs)}


def all_match(text: str, items: list):
    for item in items:
        if item not in text:
            return False
    return True


def any_match(text: str, items: list):
    for item in items:
        if item in text:
            return True
    return False


def random_pop(items: list):
    return items.pop(random.randrange(0, len(items)))


def check_sentence_by_re(sentence: str, words: list, names: list):
    for item in words:
        for n in names:
            if re.search(re.compile(item % n if '%s' in item else item), sentence):
                return True
    return False


def find_similar_list(text: str, text_list: list, _random: bool = False):
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
    SafeDumper.add_representer(
        type(None),
        lambda dumper, value: dumper.represent_scalar(u'tag:yaml.org,2002:null', '')
    )
    create_dir(path, is_file=True)

    if os.path.exists(path) and not overwrite:
        return False

    with open(path, mode='w+') as file:
        yaml.safe_dump(data, file, indent=4, default_flow_style=False, allow_unicode=True)

    return True


def create_dir(path: str, is_file: bool = False):
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


def extract_time(text: str):
    result = jionlp.ner.extract_time(text)
    if result:
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
            for k, v in time_length.items():
                if k in detail['time']:
                    return [time.localtime(time.time() + detail['time'][k] * v)]

        elif detail['type'] == 'time_period':
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
