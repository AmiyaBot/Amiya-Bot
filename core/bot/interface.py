import asyncio

from typing import *

from core import log
from core.builtin.message import Message
from core.builtin.messageChain import Chain

from core.network.mirai import HttpAdapter
from core.network.mirai.httpClient import HttpClient
from core.network.mirai.websocketClient import WebsocketClient
from core.util import Singleton
from core.config import config

from core.vars import Status, tasks

CORO = Coroutine[Any, Any, Optional[Chain]]
FUNC_CORO = Callable[[Message], CORO]


class AccountExample:
    def __init__(self, account):
        """
        status: 当前实例的状态
        complexity: 当前实例的繁忙度
        tasks: 当前bot实例的任务队列
        """
        self.account = account
        self.http = HttpClient(account)
        self.websocket = WebsocketClient(account, self.http)
        self.status = Status.DEAD
        self.complexity = 0.0
        self.tasks = []
        self.groups = []
        self.groups_status = Status.UNSYNCED

    async def action(self):
        while True:
            if self.http.status is Status.ALIVE and self.websocket.status is Status.ALIVE:
                if self.groups_status is not Status.SYNCED:
                    self.groups_status = Status.SYNCING
                    res = await self.http.get(HttpAdapter.builder('groupList', content={
                        'sessionKey': self.http.session
                    }))
                    res = res['data']
                    if res is None:
                        log.error(f'error occured when {self.account} syncing group list with HttpClient')
                        return
                    self.groups = [group['id'] for group in res]
                    self.groups_status = Status.SYNCED
                    log.info(f'{self.account} syncing group list successfully')
                if len(self.tasks) != 0:
                    await asyncio.wait(self.tasks)
            await asyncio.sleep(0.5)

    async def init(self):
        self.status = Status.ALIVE
        await self.http.init_session()
        await asyncio.wait([
            self.websocket.connect_websocket(),
            self.action()
        ])
        self.status = Status.DEAD


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

    async def dispatch_tasks(self):
        while True:
            if len(tasks) != 0:
                for group, coro in tasks:
                    bots = []
                    for bot in self.list():
                        while bot.groups_status is not Status.SYNCED:
                            await asyncio.sleep(0.1)
                        if group in bot.groups:
                            bots.append(bot)
                    bot = min(bots, key=lambda x: x.complexity)
                    bot.tasks.append(coro(bot.websocket))
                    tasks.clear()
            await asyncio.sleep(0.5)

    async def connect_all_accounts(self):
        account_coros = [self.dispatch_tasks()]
        for item in self.list():
            account_coros.append(item.init())
        await asyncio.wait(account_coros)


accounts = MultipleAccounts()
