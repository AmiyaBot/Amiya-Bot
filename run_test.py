import asyncio

from amiyabot import AmiyaBot
from amiyabot.adapters.test import test_instance

from amiya import bot as main_bot, init_task, load_resource

bot = AmiyaBot(appid='102012648', token='VtV9ld3WMhleLhKpeLizvGFGXUmHffC0', private=True)
bot.combine_factory(main_bot)

if __name__ == '__main__':
    from pluginsDev.src.arknights.operatorArchives import bot as plugin


    async def install_plugin():
        # todo 此处可以导入插件
        bot.install_plugin(plugin)
        # bot.install_plugin('plugins/amiyabot-arknights-operator-2.3.zip', extract_plugin=True)


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
