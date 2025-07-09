import copy
import time
import jieba
import datetime
import traceback

from typing import List, Coroutine, Callable

from amiyabot import *
from amiyabot.adapters import BotAdapterProtocol
from amiyabot.network.httpRequests import http_requests
from amiyahttp import HttpServer, ServerConfig
from amiyahttp.auth.authKey import AuthKey

from core.database.messages import MessageRecord
from core.database.bot import BotAccounts
from core.config import remote_config
from core.resource.botResource import BotResource
from core.resource.arknightsGameData import ArknightsGameData, ArknightsConfig
from core.lib.gitAutomation import GitAutomation
from core.util import read_yaml, create_dir

from core.plugins.customPluginInstance import Requirement, AmiyaBotPluginInstance, LazyLoadPluginInstance

create_dir('plugins')

serve_conf = read_yaml('config/server.yaml')
prefix_conf = read_yaml('config/prefix.yaml')
app_conf = ServerConfig()
app_conf.api_prefix = ''
app = HttpServer(serve_conf.host, serve_conf.port, app_conf)
allow_path = [
    '/replace/getGlobalReplace',
    '/pool/getPool',
    '/plugins'
]
auth = AuthKey(serve_conf.authKey, 'authKey', allow_path)
app.use_plugin(auth)
bot = MultipleAccounts(*BotAccounts.get_all_account())

app.add_static_folder('/plugins', 'plugins')

message_record = []


def set_prefix():
    bot.set_prefix_keywords([*prefix_conf.prefix_keywords])

    for word in prefix_conf.jieba_del_words:
        jieba.del_word(word)


def exec_before_init(coro: Callable[[], Coroutine]):
    init_task.append(coro())
    return coro

def add_allow_path(path: str):
    global auth
    auth.add_allow_path(path)


async def send_to_console_channel(chain: Chain):
    main_bot: List[BotAccounts] = BotAccounts.select().where(BotAccounts.is_main == 1)
    for item in main_bot:
        instance = bot[item.appid]

        if item.console_channel and instance:
            await instance.send_message(chain, channel_id=item.console_channel)


async def heartbeat():
    for item in bot:
        await http_requests.get(
            f'{remote_config.remote.plugin}/heartbeat?appid={item.appid}',
            ignore_error=True,
        )


async def run_main_timed_tasks():
    bot.run_timed_tasks()


@bot.message_before_handle
async def _(data: Message, factory_name: str, _):
    message_record.append(
        {
            'app_id': data.instance.appid,
            'user_id': data.user_id,
            'channel_id': data.channel_id,
            'msg_type': data.message_type or 'channel',
            'classify': 'call',
            'create_time': int(time.time()),
        }
    )


@bot.on_exception()
async def _(err: Exception, instance: BotAdapterProtocol, data: Union[Message, Event]):
    info = [
        'Adapter: ' + str(instance),
        'Bot: ' + str(instance.appid),
        'Channel: ' + str(data.channel_id),
        'User: ' + str(data.user_id),
        '\n' + (data.text if isinstance(data, Message) else data.event_name),
    ]

    content = Chain().text('\n'.join(info)).text_image(traceback.format_exc())

    await send_to_console_channel(content)


@bot.timed_task(each=60)
async def _(_):
    global message_record
    MessageRecord.batch_insert(copy.deepcopy(message_record))
    message_record = []


@bot.timed_task(each=60, run_when_added=True)
async def _(_):
    await heartbeat()


@bot.timed_task(each=3600, run_when_added=True)
async def _(_):
    timestamp = int(
        time.mktime(
            time.strptime(
                (datetime.datetime.now() + datetime.timedelta(days=-90)).strftime('%Y%m%d'),
                '%Y%m%d',
            )
        )
    )
    MessageRecord.delete().where(MessageRecord.create_time < timestamp).execute()


init_task = [heartbeat(), run_main_timed_tasks()]
set_prefix()
