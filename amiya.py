import os
import sys
import asyncio
import core.frozen

from core import app, bot, init_task, load_resource, load_plugins

sys.path += [
    os.path.dirname(sys.executable),
    os.path.dirname('resource/env/python-dlls'),
    os.path.dirname('resource/env/python-standard-lib.zip'),
]

# async def plugin_test():
#     from pluginsDev.arknights.operatorArchives import bot as plugin
#
#     bot.install_plugin(plugin)


if __name__ == '__main__':
    try:
        load_resource()
        asyncio.run(
            asyncio.wait(
                [
                    *init_task,
                    bot.start(enable_chromium=True),
                    app.serve(),
                    load_plugins(),
                    # plugin_test()
                ]
            )
        )
    except KeyboardInterrupt:
        pass
