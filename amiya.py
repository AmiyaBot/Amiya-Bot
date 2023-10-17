import os
import sys
import asyncio
import core.frozen

from typing import Coroutine
from core.plugins import PluginsLoader
from core import app, bot, init_task, BotResource


def run_amiya(*tasks: Coroutine):
    try:
        BotResource.download_bot_resource()

        sys.path += [
            os.path.dirname(sys.executable),
            os.path.dirname('resource/env/python-dlls'),
            os.path.dirname('resource/env/python-standard-lib.zip'),
        ]

        asyncio.run(asyncio.wait([*init_task, *tasks]))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    loader = PluginsLoader(bot)
    asyncio.run(loader.load_local_plugins())
    run_amiya(bot.start(launch_browser=True), app.serve())
