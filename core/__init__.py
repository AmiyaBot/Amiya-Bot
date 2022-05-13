import asyncio

from typing import Dict

from core.builtin.lib.htmlConverter import ChromiumBrowser
from core.builtin.timedTask import TasksControl
from core.builtin.message import Message, Event
from core.builtin.messageChain import Chain, custom_chain
from core.builtin.messageHandler import speed
from core.builtin.message.mirai import Mirai

from core.database.messages import MessageStack
from core.network.mirai.httpClient import HttpClient
from core.network.mirai.websocketClient import WebsocketClient
from core.util import Singleton
from core.config import config

from core.resource.botResource import BotResource
from core.resource.arknightsGameData import ArknightsGameDataResource, ArknightsGameData


class AccountExample:
    def __init__(self, account):
        self.account = account
        self.http = HttpClient(account)
        self.websocket = WebsocketClient(account, self.http)

    async def init(self):
        await self.http.init_session()
        await self.websocket.connect_websocket()


class AccountExampleNotFound(Exception):
    def __init__(self, account):
        self.account = account

    def __str__(self):
        return f'can not found account "{self.account}" in MultipleAccount'


class MultipleAccounts(metaclass=Singleton):
    def __init__(self):
        self.examples: Dict[str, AccountExample] = dict()

        for item in config.miraiApiHttp.account:
            self.examples[str(item)] = AccountExample(item)

    def __call__(self, account):
        if str(account) in self.examples:
            return self.examples[str(account)]
        raise AccountExampleNotFound(account)

    def list(self):
        for _, example in self.examples.items():
            yield example

    async def connect_all_accounts(self):
        for item in self.list():
            await item.init()


init_task = []
accounts = MultipleAccounts()


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
