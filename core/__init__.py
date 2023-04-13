import os
import re
import copy
import time
import jieba
import datetime
import traceback
import configparser

from typing import List, Union
from amiyabot import (
    MultipleAccounts,
    HttpServer,
    Message,
    Event,
    Equal,
    Chain,
    ChainBuilder,
    log
)
from amiyabot.adapters import BotAdapterProtocol
from amiyabot.adapters.tencent import TencentBotInstance
from amiyabot.network.httpRequests import http_requests
from amiyabot.builtin.lib.timedTask import tasks_control
from amiyabot.util import extract_zip

from core.database.messages import MessageRecord
from core.database.bot import BotAccounts, Admin
from core.resource import remote_config
from core.resource.botResource import BotResource
from core.resource.arknightsGameData import ArknightsGameData, ArknightsConfig
from core.lib.gitAutomation import GitAutomation
from core.util import read_yaml, create_dir

from core.customPluginInstance import AmiyaBotPluginInstance, LazyLoadPluginInstance

serve_conf = read_yaml('config/server.yaml')
prefix_conf = read_yaml('config/prefix.yaml')

app = HttpServer(serve_conf.host, serve_conf.port, auth_key=serve_conf.authKey)
bot = MultipleAccounts(*BotAccounts.get_all_account())

message_record = []


def set_prefix():
    bot.set_prefix_keywords(*prefix_conf.prefix_keywords)

    for word in prefix_conf.jieba_del_words:
        jieba.del_word(word)


def load_resource():
    gamedata_path = 'resource/gamedata'

    GitAutomation(gamedata_path, remote_config.remote.gamedata).update(['--depth 1'])

    if os.path.exists(f'{gamedata_path}/.gitmodules'):
        config = configparser.ConfigParser()
        config.read(f'{gamedata_path}/.gitmodules', encoding='utf-8')

        for submodule in config.values():
            path = submodule.get('path')
            url = submodule.get('url')
            if path:
                folder = f'{gamedata_path}/{path}'
                GitAutomation(folder, url).update(['--depth 1'])
                for root, _, files in os.walk(folder):
                    for file in files:
                        r = re.search(r'splice_\d+\.zip', file)
                        if r:
                            extract_zip(os.path.join(root, file), folder + '/skin', overwrite=True)

    BotResource.download_bot_resource()
    ArknightsConfig.initialize()
    ArknightsGameData.initialize()


async def load_plugins():
    create_dir('plugins')
    count = 0
    for root, dirs, files in os.walk('plugins'):
        for file in files:
            if file.endswith('.zip'):
                log.info(f'installing plugin {file}')
                try:
                    res = bot.install_plugin(os.path.join(root, file), extract_plugin=True)
                    if res:
                        count += 1
                except Exception as e:
                    log.error(e, 'plugin install error:')
        break

    # 然后对所有插件执行懒加载（如果有的话）
    for plugin_id, item in bot.plugins.items():
        if isinstance(item, LazyLoadPluginInstance):
            item.load()

    if count:
        log.info(f'successfully loaded {count} plugin(s).')


class SourceServer(ChainBuilder):
    @staticmethod
    async def image_getter_hook(image):
        if type(image) is bytes:
            res = await http_requests.post_upload(f'{remote_config.remote.resource}/upload', image)
            if res:
                return f'{remote_config.remote.resource}/images?path=' + res.strip('"')
        return image


def exec_before_init(coro):
    init_task.append(coro())
    return coro


async def send_to_console_channel(chain: Chain):
    main_bot: List[BotAccounts] = BotAccounts.select().where(BotAccounts.is_main == 1)
    for item in main_bot:
        if item.console_channel:
            await bot[item.appid].send_message(chain, channel_id=item.console_channel)


async def heartbeat():
    for item in bot:
        await http_requests.get(f'https://server.amiyabot.com:8020/heartbeat?appid={item.appid}', ignore_error=True)


@bot.message_created
async def _(data: Message, _):
    if not data.is_admin:
        data.is_admin = bool(Admin.get_or_none(account=data.user_id))


@bot.message_before_handle
async def _(data: Message, factory_name: str, _):
    message_record.append({
        'app_id': data.instance.appid,
        'user_id': data.user_id,
        'channel_id': data.channel_id,
        'msg_type': data.message_type or 'channel',
        'classify': 'call',
        'create_time': int(time.time())
    })


@bot.on_exception()
async def _(err: Exception, instance: BotAdapterProtocol, data: Union[Message, Event]):
    chain = Chain()

    if type(instance) is TencentBotInstance:
        chain.builder = SourceServer()

    info = [
        'Adapter: ' + str(instance),
        'Bot: ' + str(instance.appid),
        'Channel: ' + str(data.channel_id),
        'User: ' + str(data.user_id),
        '\n' + data.text
    ]

    content = chain.text('\n'.join(info)).text_image(traceback.format_exc())

    await send_to_console_channel(content)


@tasks_control.timed_task(each=60)
async def _():
    await heartbeat()


@tasks_control.timed_task(each=60)
async def _():
    global message_record
    MessageRecord.batch_insert(copy.deepcopy(message_record))
    message_record = []


@tasks_control.timed_task(each=3600)
async def _():
    timestamp = int(
        time.mktime(
            time.strptime(
                (datetime.datetime.now() + datetime.timedelta(days=-7)).strftime('%Y%m%d'),
                '%Y%m%d'
            )
        )
    )
    MessageRecord.delete().where(MessageRecord.create_time < timestamp).execute()


init_task = [
    heartbeat(),
    tasks_control.run_tasks()
]
