import time
import asyncio

from amiyabot import AmiyaBot, Message, Event, Chain
from amiyabot.util import run_in_thread_pool, random_code, create_dir
from amiyabot.handler import BotAdapterProtocol
from amiyabot.adapters.convert import text_convert
from amiyabot.builtin.messageChain.element import Text, Html

from amiya import init_task, load_resource


class TestInstance(BotAdapterProtocol):
    def __int__(self, appid: str, token: str):
        super().__init__(appid, token)

    def close(self):
        ...

    async def connect(self, private: bool, handler):
        while True:
            await asyncio.sleep(0)
            # todo 在此处模拟接收到的数据
            event = 'test'
            data = {
                'message': await run_in_thread_pool(input)
            }
            asyncio.create_task(handler(event, data))

    async def send_message(self,
                           chain: Chain,
                           user_id: str = '',
                           channel_id: str = '',
                           direct_src_guild_id: str = ''):
        data = Message(self)

        data.user_id = user_id
        data.channel_id = channel_id
        data.message_type = 'group'

        if not channel_id and not user_id:
            raise TypeError(
                'send_message() missing argument: "channel_id" or "user_id"')

        if not channel_id and user_id:
            data.message_type = 'private'
            data.is_direct = True

        message = Chain(data)
        message.chain = chain.chain
        message.builder = chain.builder

        await self.send_chain_message(message)

    async def send_chain_message(self, chain: Chain):
        # todo 在此处模拟输出

        for item in chain.chain:
            if type(item) is Text and item.content.strip('\n'):
                print(item.content)

            if type(item) is Html:
                filename = f'log/images/{time.time() * 1000}{random_code(10)}.png'
                create_dir(filename, is_file=True)
                with open(filename, mode='wb') as f:
                    f.write(await item.create_html_image())
                print('image:', filename)

    async def package_message(self, event: str, message: dict):
        # todo 在此处模拟封包，输出 Message 或 Event 对象
        text = message['message']
        data = Message(self, message)

        data.user_id = 'test_user'
        data.channel_id = 'test_group'
        data.message_type = 'group'
        data.nickname = 'admin'

        data.is_admin = True

        return text_convert(data, text, text)


bot = AmiyaBot(appid='', token='', adapter=TestInstance)

if __name__ == '__main__':
    from pluginsDev.src.arknights.operatorArchives import bot as plugin


    async def install_plugin():
        # todo 此处可以导入插件
        bot.install_plugin(plugin)
        # bot.install_plugin('plugins/amiyabot-arknights-operator-1.5.zip', extract_plugin=True)


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
