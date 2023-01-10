import asyncio

from amiyabot import AmiyaBot
from amiyabot.adapters.mirai import mirai_api_http

from amiya import init_task, load_resource

bot = AmiyaBot(appid='2533207617', token='AmiyaBot',
               adapter=mirai_api_http(host='119.29.87.110', http_port=8080, ws_port=8060))

if __name__ == '__main__':
    # from pluginsDev.src.user import bot as plugin


    async def install_plugin():
        # todo 此处可以导入插件
        # bot.install_plugin(plugin)
        bot.install_plugin('plugins/amiyabot-arknights-operator-2.3.zip', extract_plugin=True)


    bot.set_prefix_keywords('兔兔')
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
