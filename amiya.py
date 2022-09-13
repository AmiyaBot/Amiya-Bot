import srsly
import frozen
import server
import asyncio
import functions

from core import app, bot, init_task, load_task

if __name__ == '__main__':
    try:
        load_task()
        asyncio.run(
            asyncio.wait(
                [
                    *init_task,
                    bot.start(enable_chromium=True),
                    app.serve()
                ]
            )
        )
    except KeyboardInterrupt:
        pass
