import asyncio

from typing import *

from core.bot import accounts
from core.builtin.lib.htmlConverter import ChromiumBrowser
from core.builtin.timedTask import TasksControl
from core.builtin.message import Message, Event
from core.builtin.messageChain import Chain, custom_chain
from core.builtin.messageHandler import speed
from core.builtin.message.mirai import Mirai

from core.database.messages import MessageStack
from core.network.mirai import WebsocketAdapter
from core.network.mirai.httpClient import HttpClient
from core.network.mirai.websocketClient import WebsocketClient
from core.util import Singleton
from core.config import config

from core.resource.botResource import BotResource
from core.resource.arknightsGameData import ArknightsGameDataResource, ArknightsGameData

CORO = Coroutine[Any, Any, Optional[Chain]]
FUNC_CORO = Callable[[Message], CORO]


init_task = []


def exec_before_init(coro):
    init_task.append(coro())
    return coro


async def initialization():
    BotResource.download_bot_resource()
    BotResource.download_amiya_bot_console()
    ArknightsGameDataResource.download_gamedata_files()

    await asyncio.wait(init_task)
    await asyncio.wait([
        speed.clean_container(),
        MessageStack.run_recording(),
        TasksControl.run_tasks(),
        accounts.connect_all_accounts(),
        ChromiumBrowser().launch()
    ])
