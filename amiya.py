import asyncio
import functions

from core.network.httpServer import HttpServer
from core.control import StateControl
from core.util import read_yaml
from core.bot import BotHandlers
from core import log, init_core

BotHandlers.add_prefix(
    read_yaml('config/private/talking.yaml').call.positive
)


class AmiyaBot:
    def __init__(self):
        log.info(
            [
                f'starting Amiya-Bot...',
                f'%d function module(s) loaded.' % len([f for f in dir(functions) if f.startswith('__')])
            ] + BotHandlers.detail()
        )

        StateControl.start()

        self.tasks = init_core()

    async def run(self):
        await asyncio.wait(self.tasks)
        log.info('AmiyaBot shutdown.')


async def bot_run_forever():
    while StateControl.keep_running:
        await AmiyaBot().run()


if __name__ == '__main__':
    console_server = HttpServer()

    asyncio.run(
        asyncio.wait(
            [
                bot_run_forever(),
                console_server.serve()
            ]
        )
    )
