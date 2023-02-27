import asyncio

from amiyabot import AmiyaBot
from amiyabot.adapters.test import test_instance

from amiya import init_task, load_resource

bot = AmiyaBot(appid='test', token='', adapter=test_instance('127.0.0.1', 32001))

if __name__ == '__main__':
    from pluginDev.src.arknights.operatorArchives import bot as plugin


    async def install_plugin():
        # todo 此处可以导入插件
        bot.install_plugin(plugin)
        # bot.install_plugin('plugins/amiyabot-arknights-operator-2.3.zip', extract_plugin=True)


    bot.set_prefix_keywords(['兔兔', '阿米娅', 'amiya'])
    try:
        load_resource()
        asyncio.run(
            asyncio.wait(
                [
                    *init_task,
                    bot.start(launch_browser=True),
                    install_plugin()
                ]
            )
        )
    except KeyboardInterrupt:
        pass
