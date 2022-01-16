import asyncio
import functions

from core import core_tasks, log
from core.network.httpServer import server
from core.database.messages import MessageStack
from core.builtin.messageHandler import speed
from core.control import StateControl
from core.bot import BotHandlers

BotHandlers.add_prefix(
    [
        '阿米娅',
        '阿米兔',
        '兔兔',
        '兔子',
        '小兔子',
        'Amiya',
        'amiya'
    ]
)


class AmiyaBot:
    def __init__(self):
        log.info('starting AmiyaBot...')
        log.info(f'%d function file(s) loaded.' % len([f for f in dir(functions) if f[:2] != '__']))

        StateControl.start()

        super().__init__()

        self.tasks = core_tasks() + [
            MessageStack.run()
        ]

    async def run(self):
        await asyncio.wait(self.tasks)
        log.info('AmiyaBot shutdown.')


async def bot_run_forever():
    while StateControl.keep_running:
        await AmiyaBot().run()


if __name__ == '__main__':
    asyncio.run(
        asyncio.wait(
            [
                bot_run_forever(),
                speed.clean_container(),
                server.serve()
            ]
        )
    )
