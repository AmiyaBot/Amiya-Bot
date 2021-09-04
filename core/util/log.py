import os
import time
import jieba
import shutil
import datetime
import traceback

from ..util.common import make_folder

log_path = 'log'

jieba.setLogLevel(jieba.logging.INFO)


def info(msg: str, title: str = 'info', alignment: bool = True, log: bool = True):
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    front = f'[{date}]' \
            f'[{title.upper()}]' \
            f'{" " if msg[0] != "[" else ""}'

    text = capitalize(msg)
    if alignment:
        text = text.replace('\n', '\n' + ' ' * len(front))
    text = front + text

    print(text)

    if log:
        write_in_log(text)


def error(msg: str):
    info(msg, title='error', alignment=False)


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
