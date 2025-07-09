import os
import sys
import asyncio
import core.frozen

from typing import Coroutine, List
from core.plugins import PluginsLoader
from core import app, bot, init_task, BotResource


def run_amiya(tasks: List[Coroutine] = []):
    async def main():
        loader = PluginsLoader(bot)
        await loader.load_local_plugins()
        
        # Convert coroutines to tasks for asyncio.wait()
        all_tasks = [asyncio.create_task(task) for task in [*init_task, *tasks]]
        await asyncio.wait(all_tasks)
    
    try:
        BotResource.download_bot_resource()

        sys.path += [
            os.path.dirname(sys.executable),
            os.path.abspath('resource/env/python-dlls'),
            os.path.abspath('resource/env/python-standard-lib.zip'),
        ]
        
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    run_amiya([bot.start(launch_browser=True), app.serve()])
