import asyncio
import functions

from core.database.messages import MessageStack
from core.network.httpServer import server
from core.builtin.messageHandler import speed
from core.builtin.timedTask import TasksControl
from core.control import StateControl
from core.bot import BotHandlers
from core import (log,
                  websocket,
                  network)

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
        log.info(
            [
                f'starting Amiya-Bot...',
                f'%d function file(s) loaded.' % len([f for f in dir(functions) if f[:2] != '__'])
            ] + BotHandlers.detail()
        )

        StateControl.start()

        super().__init__()

        self.tasks = network() + [
            speed.clean_container(),
            MessageStack.run_recording(),
            TasksControl.run_tasks(websocket)
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
                server.serve()
            ]
        )
    )
