import os
import json
import time

from amiyabot import PluginInstance
from amiyabot.adapters.convert import text_convert
from amiyabot.adapters.tencent import TencentBotInstance
from amiyabot.network.httpRequests import http_requests
from core.database.bot import *
from core.lib.baiduCloud import BaiduCloud
from core.resource import remote_config
from core.util import read_yaml, extract_plugin
from core import log, exec_before_init, Message, Chain

curr_dir = os.path.dirname(__file__)
replace_plugin = 'resource/plugins/replace'

if curr_dir.endswith('.zip'):
    extract_plugin(curr_dir, replace_plugin)
else:
    replace_plugin = curr_dir

baidu = BaiduCloud(read_yaml(f'{replace_plugin}/baiduCloud.yaml'))
bot = PluginInstance(
    name='词语替换',
    version='1.0',
    plugin_id='amiyabot-replace'
)


@exec_before_init
async def sync_replace(force: bool = False):
    if not force:
        if TextReplace.get_or_none():
            return False

    res = await http_requests.get(remote_config.remote.console + '/replace/getReplace')
    if res:
        async with log.catch('replace sync error:'):
            res = json.loads(res)

            TextReplace.truncate_table()
            TextReplace.batch_insert(res['data'])

            return True


@bot.handler_middleware
async def _(data: Message):
    replace: List[TextReplace] = TextReplace.select() \
        .where(TextReplace.group_id == data.guild_id, TextReplace.is_active == 1) \
        .orwhere(TextReplace.is_global == 1)

    if not data.is_admin:
        data.is_admin = bool(Admin.get_or_none(account=data.user_id))

    if replace:
        text = data.text_origin
        for item in reversed(list(replace)):
            text = text.replace(item.replace, item.origin)

        return text_convert(data, text, data.text_origin)


@bot.on_message(keywords=['别名'], level=5)
async def _(data: Message):
    if type(data.instance) is TencentBotInstance:
        if not data.is_admin:
            return Chain(data).text('抱歉博士，别名功能只能由管理员使用')

    is_super = bool(Admin.get_or_none(account=data.user_id))

    search_text = data.text_initial

    for item in bot.prefix_keywords:
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
            TextReplace.delete().where(TextReplace.group_id == data.guild_id,
                                       TextReplace.replace == replace).execute()
            return Chain(data).text(f'已在本频道删除别名 [{replace}]')

        # 检查全局别名是否存在
        exist: TextReplace = TextReplace.get_or_none(replace=replace, is_global=1)
        if exist:
            text = f'[{origin}] 全局别名识别已存在 [{replace}] '
            if exist.is_active == 0:
                text += '（未审核通过）'
            return Chain(data).text(text)

        # 检查本频道别名是否存在
        exist: TextReplace = TextReplace.get_or_none(group_id=data.guild_id, replace=replace)
        if exist:
            text = f'本频道 [{origin}] 别名识别已存在 [{replace}] '
            if exist.is_active == 0:
                text += '（未审核通过）'
            return Chain(data).text(text)

        # 超管不需要审核
        if is_super:
            return save_replace(data, origin, replace, is_global=1)

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
        if baidu.enable:
            check = await baidu.text_censor(replace)

            if not check:
                return Chain(data).text('审核失败...')

            if check['conclusionType'] == 2:
                text = '审核不通过！检测到以下违规内容：\n'
                for item in check['data']:
                    text += item['msg'] + '\n'

                return Chain(data).text(text)
            else:
                return save_replace(data, origin, replace)

        return save_replace(data, origin, replace)


def show_replace_by_replace(data: Message, replace):
    replace_list: List[TextReplace] = TextReplace.select().where(TextReplace.group_id == data.guild_id,
                                                                 TextReplace.origin == replace)
    if replace_list:
        text = f'找到 [{replace}] 在本频道生效的别名:\n'
        for item in replace_list:
            text += f'{item.replace}{"（审核通过）" if item.is_active else "（未审核通过）"}\n'
        return Chain(data).text(text.strip('、'))
    else:
        return Chain(data).text(f'没有找到 [{replace}] 在本频道生效的别名')


def check_forbidden(replace, origin):
    if replace.isdigit():
        return replace

    replace_setting: List[TextReplaceSetting] = TextReplaceSetting.select().where(TextReplaceSetting.status == 1)

    if replace in [item.text for item in replace_setting] + ['别名']:
        return replace

    for item in bot.prefix_keywords:
        if item in [replace, origin]:
            return item

    keyword_dicts = [
        'enemies.txt',
        'materials.txt',
        'operators.txt',
        'skins.txt',
        'stages.txt',
        'stories.txt',
        'tags.txt',
        'tokens.txt'
    ]

    for file in keyword_dicts:
        if not os.path.exists(f'resource/{file}'):
            continue
        with open(f'resource/{file}', mode='r', encoding='utf-8') as src:
            content = src.read().strip('\n').split('\n')
        for item in content:
            item = item.replace(' 500 n', '')
            if item == replace:
                return item


def check_permissible(text):
    replace_setting: List[TextReplaceSetting] = TextReplaceSetting.select().where(TextReplaceSetting.status == 0)
    return text in [item.text for item in replace_setting]


def save_replace(data: Message, origin, replace, is_global=0):
    TextReplace.create(
        user_id=data.user_id,
        group_id=data.guild_id,
        origin=origin,
        replace=replace,
        in_time=int(time.time()),
        is_global=is_global
    )
    return Chain(data).text(f'审核通过！%s将使用 [{replace}] 作为 [{origin}] 的别名' % ('本频道' if not is_global else '全局'))
