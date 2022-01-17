import re
import time

from core.database.group import *
from core.builtin.baiduCloud import BaiduCloud
from core.builtin.message.mirai import text_convert
from core import bot, Message, Chain

baidu = BaiduCloud()


@table
class TextReplace(BaseModel):
    user_id = TextField()
    group_id = TextField()
    origin = TextField()
    replace = TextField()
    in_time = BigIntegerField()
    is_global = IntegerField(default=0)
    is_active = IntegerField(default=1)


@bot.handle_message
async def _(data: Message):
    replace: List[TextReplace] = TextReplace.select() \
        .where(TextReplace.group_id == data.group_id, TextReplace.is_active == 1) \
        .orwhere(TextReplace.is_global == 1)

    if replace:
        for item in reversed(list(replace)):
            text = data.text_origin.replace(item.replace, item.origin)
            return text_convert(data, text)


@bot.on_group_message(function_id='textReplace', keywords='别名')
async def _(data: Message):
    search_text = data.text_origin

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

        # 检查别名是否存在
        exist: TextReplace = TextReplace.get_or_none(group_id=data.group_id, replace=replace)
        if exist:
            text = f'本群 [{origin}] 别名识别已存在 [{replace}] '
            if exist.is_active == 0:
                text += '（未审核通过）'
            return Chain(data).text(text)

        # 开始审核...
        await data.send(Chain(data, quote=False).text('正在审核，博士请稍等...'))

        # 检查原生词语和设置禁止的词语
        # if not self.check_forbidden(replace) or not self.check_name(origin):
        #     return Chain(data).text(f'审核不通过！检测到存在禁止替换的内容')

        # 白名单可直接通过审核
        # if self.check_permissible(replace):
        #     return self.save_replace(data, origin, replace)

        # 百度审核
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


def save_replace(data: Message, origin, replace):
    TextReplace.create(
        user_id=data.user_id,
        group_id=data.group_id,
        origin=origin,
        replace=replace,
        in_time=int(time.time())
    )
    return Chain(data).text(f'审核通过！本群将使用 [{replace}] 作为 [{origin}] 的别名')
