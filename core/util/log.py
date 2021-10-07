import os
import sys
import time
import jieba
import shutil
import datetime
import traceback

from typing import Union

from ..util.common import make_folder

log_path = 'log'
jieba.setLogLevel(jieba.logging.INFO)


class StatusCalculator:
    def __init__(self):
        self.res = {
            'success': 0,
            'fail': 0
        }
        self.total = 0

    def set_res(self, res):
        if res:
            self.success()
        else:
            self.fail()

    def success(self):
        self.res['success'] += 1

    def fail(self):
        self.res['fail'] += 1


def download_src(data: Union[dict, list], title: str = 'data', _total=True, _record=True):
    data = data.keys() if type(data) is dict else data
    status = StatusCalculator()
    success = 0

    if _total:
        status.total = len(data)

    if not len(data):
        return None

    def print_bar(i):
        nonlocal success

        date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        curr = int(i / len(data) * 100)
        block = int(curr / 4)
        bar = '=' * block + ' ' * (25 - block)

        success = status.res['success']
        fail = status.res['fail']

        print('\r', end='')
        print(
            f'[{date}][INFO] [{bar}] {curr}% {i}/{len(data)} '
            f'({status.total} TT, {success} OK, {fail} NG) <{title}>',
            end=''
        )

        sys.stdout.flush()

    print_bar(0)
    for index, item in enumerate(data):
        yield item, status
        print_bar(index + 1)

    print()
    if _record:
        with open(f'resource/.src', mode='a+') as src:
            src.write(f'{title}\t{success}/{status.total}\n')


def info(msg: str, title: str = 'info', alignment: bool = True, log: bool = True, stdout=print):
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    front = f'[{date}]' \
            f'[{title.upper()}]' \
            f'{" " if msg[0] != "[" else ""}'

    text = capitalize(msg)
    if alignment:
        text = text.replace('\n', '\n' + ' ' * len(front))
    text = front + text

    if stdout:
        stdout(text)

    if log:
        write_in_log(text)

    return text


def error(msg: str, stdout=print):
    info(msg, title='error', alignment=False, stdout=stdout)


def capitalize(text: str):
    return text[0].upper() + text[1:]


def today_log(index=-1, title='running'):
    path = f'{log_path}/{title}'
    file = time.strftime('%Y%m%d', time.localtime()) + '.log'

    make_folder(path)

    t = path, f'{path}/{file}'

    return t if index == -1 else t[index]


def write_in_log(text):
    # noinspection PyBroadException
    try:
        with open(today_log(1), encoding='utf-8', mode='a+') as log:
            log.write(text + '\n')
    except Exception:
        info(traceback.format_exc(), title='error', log=False)


def clean_log(days, extra: list = None):
    day_ago = datetime.datetime.now() - datetime.timedelta(days=int(days))
    day_ago = int(day_ago.strftime('%Y%m%d'))

    path = today_log(0)

    for root, dirs, files in os.walk(path):
        for item in files:
            filename = int(item.split('.')[0])
            if filename < day_ago:
                os.remove(os.path.join(root, item))

    if extra:
        for item in extra:
            if os.path.exists(item):
                shutil.rmtree(item)
