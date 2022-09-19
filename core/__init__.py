import os
import traceback

from typing import List
from amiyabot import MultipleAccounts, HttpServer, Message, Chain, ChainBuilder, Equal, log
from amiyabot.adapters import BotAdapterProtocol
from amiyabot.adapters.tencent import TencentBotInstance
from amiyabot.network.httpRequests import http_requests

from core.database.bot import BotAccounts
from core.resource import remote_config
from core.resource.botResource import BotResource
from core.resource.arknightsGameData import ArknightsGameData, ArknightsConfig
from core.resource.arknightsGameData.penguin import save_penguin_data
from core.lib.gitAutomation import GitAutomation
from core.lib.timedTask import TasksControl
from core.util import read_yaml, create_dir

serve_conf = read_yaml('config/server.yaml')

app = HttpServer(serve_conf.host, serve_conf.port, auth_key=serve_conf.authKey)
bot = MultipleAccounts(*BotAccounts.get_all_account())

bot.set_prefix_keywords(list(read_yaml('config/bot.yaml').callName))

gamedata_repo = GitAutomation('resource/gamedata', remote_config.remote.gamedata)
tasks_control = TasksControl()


def load_resource():
    gamedata_repo.update()
    BotResource.download_bot_resource()
    ArknightsConfig.initialize()
    ArknightsGameData.initialize()


def load_plugins():
    create_dir('plugins')
    count = 0
    for root, dirs, files in os.walk('plugins'):
        for file in files:
            if file.endswith('.zip'):
                res = bot.install_plugin(os.path.join(root, file))
                if res:
                    count += 1

    if count:
        log.info(f'successfully loaded {count} plugin(s).')


init_task = [
    save_penguin_data(),
    tasks_control.run_tasks()
]


class SourceServer(ChainBuilder):
    @staticmethod
    async def image_getter_hook(image):
        if type(image) is bytes:
            res = await http_requests.upload(f'{remote_config.remote.resource}/upload', image)
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


@bot.on_exception()
async def _(err: Exception, instance: BotAdapterProtocol):
    chain = Chain()

    if type(instance) is TencentBotInstance:
        chain.builder = SourceServer()

    content = chain.text(f'{str(instance)} Bot: {instance.appid}').text_image(traceback.format_exc())

    await send_to_console_channel(content)
