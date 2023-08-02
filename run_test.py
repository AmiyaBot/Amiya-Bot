from amiyabot import AmiyaBot
from amiyabot.adapters.test import test_instance

from amiya import bot as main_bot, run_amiya

bot = AmiyaBot(appid='test', token='', adapter=test_instance('127.0.0.1', 32001))
bot.combine_factory(main_bot)

if __name__ == '__main__':
    # 导入比较核心的插件
    from pluginsDev.src.arknights.arknightsGameData import bot as resource
    from pluginsDev.src.replace import bot as replace

    # 导入测试的插件
    from pluginsDev.src.arknights.operatorArchives import bot as plugin


    async def install_plugin():
        # 安装插件
        bot.install_plugin(resource)
        bot.install_plugin(replace)
        bot.install_plugin(plugin)

        # 也可以通过文件安装
        # bot.install_plugin('plugins/amiyabot-arknights-gamedata-1.0.zip', extract_plugin=True)


    run_amiya(
        bot.start(launch_browser=True),
        install_plugin()
    )
