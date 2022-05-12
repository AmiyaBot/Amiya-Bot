import time

from core.database.group import *
from core.database.bot import TextReplace, TextReplaceSetting
from core.builtin.baiduCloud import BaiduCloud
from core.builtin.message.build import text_convert
from core import bot, Message, Chain

baidu = BaiduCloud()


@bot.handler_middleware
async def _(data: Message):
    replace: List[TextReplace] = TextReplace.select() \
        .where(TextReplace.group_id == data.group_id, TextReplace.is_active == 1) \
        .orwhere(TextReplace.is_global == 1)

    if replace:
        text = data.text_origin
        for item in reversed(list(replace)):
            text = text.replace(item.replace, item.origin)

        return text_convert(data, text, data.text_origin)


@bot.on_group_message(function_id='textReplace', keywords=['别名'], level=5)
async def _(data: Message):
    search_text = data.text_initial

    for item in bot.BotHandlers.prefix_keywords:
        if search_text.startswith(item):
            search_text = search_text.replace(item, '', 1)
            break

    r = re.search(r'(\S+)别名(\S+)', search_text)
    if r:
        origin = r.group(1)
        replace = r.group(2)

        if '查看' in data.text_origin:
            return show_replace_by_replace(data, replace)

        if origin == '删除':
            TextReplace.delete().where(TextReplace.group_id == data.group_id,
                                       TextReplace.replace == replace).execute()
            return Chain(data).text(f'已在本群删除别名 [{replace}]')

        # 检查全局别名是否存在
        exist: TextReplace = TextReplace.get_or_none(replace=replace, is_global=1)
        if exist:
            text = f'[{origin}] 全局别名识别已存在 [{replace}] '
            if exist.is_active == 0:
                text += '（未审核通过）'
            return Chain(data).text(text)

        # 检查本群别名是否存在
        exist: TextReplace = TextReplace.get_or_none(group_id=data.group_id, replace=replace)
        if exist:
            text = f'本群 [{origin}] 别名识别已存在 [{replace}] '
            if exist.is_active == 0:
                text += '（未审核通过）'
            return Chain(data).text(text)

        # 开始审核...
        await data.send(Chain(data).text('正在审核，博士请稍等...'))

        # 检查原生词语和设置禁止的词语，禁止使用数字替换词
        forbidden = check_forbidden(replace, origin)
        if forbidden:
            return Chain(data).text(f'审核不通过！检测到存在禁止替换的内容：{forbidden}')

        # 白名单可直接通过审核
        if check_permissible(replace):
            return save_replace(data, origin, replace)

        # 百度审核
        check = None
        if baidu.enable:
            check = await baidu.text_censor(replace)

        if not check or check['conclusionType'] in [3, 4]:
            TextReplace.create(
                user_id=data.user_id,
                group_id=data.group_id,
                origin=origin,
                replace=replace,
                in_time=int(time.time()),
                is_active=0
            )
            text = ''
            if check and check['conclusionType'] == 3:
                for item in check['data']:
                    text += item['msg'] + '\n'

            return Chain(data).text(f'已转由管理员审核，请等待管理员确认批准\n{text}')
        else:
            if check['conclusionType'] == 2:
                text = '审核不通过！检测到以下违规内容：\n'
                for item in check['data']:
                    text += item['msg'] + '\n'

                return Chain(data).text(text)

            if check['conclusionType'] == 1:
                return save_replace(data, origin, replace)


def show_replace_by_replace(data: Message, replace):
    replace_list = TextReplace.select().where(TextReplace.group_id == data.group_id,
                                              TextReplace.origin == replace)
    if replace_list:
        text = f'找到 [{replace}] 在本群生效的别名:\n'
        for item in replace_list:
            item: TextReplace
            text += f'{item.replace}{"（审核通过）" if item.is_active else "（未审核通过）"}\n'
        return Chain(data).text(text.strip('、'))
    else:
        return Chain(data).text(f'没有找到 [{replace}] 在本群生效的别名')


def check_forbidden(replace, origin):
    if replace.isdigit():
        return replace

    replace_setting: List[TextReplaceSetting] = TextReplaceSetting.select().where(TextReplaceSetting.status == 1)

    if replace in [item.text for item in replace_setting] + ['别名']:
        return replace

    for item in bot.BotHandlers.prefix_keywords:
        if item in [replace, origin]:
            return item

    for file in [
        'enemies.txt',
        'materials.txt',
        'operators.txt',
        'skins.txt',
        'stories.txt',
        'tags.txt'
    ]:
        with open(f'resource/{file}', mode='r', encoding='utf-8') as src:
            content = src.read().strip('\n').split('\n')
        for item in content:
            item = item.replace(' 500 n', '')
            if item == replace:
                return item


def check_permissible(text):
    replace_setting: List[TextReplaceSetting] = TextReplaceSetting.select().where(TextReplaceSetting.status == 0)
    return text in [item.text for item in replace_setting]


def save_replace(data: Message, origin, replace):
    TextReplace.create(
        user_id=data.user_id,
        group_id=data.group_id,
        origin=origin,
        replace=replace,
        in_time=int(time.time())
    )
    return Chain(data).text(f'审核通过！本群将使用 [{replace}] 作为 [{origin}] 的别名')
