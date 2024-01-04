from typing import Optional

from core import app, bot
from core.database.bot import BotAccounts, query_to_list
from amiyabot.network.httpServer import BaseModel
from amiyabot import AmiyaBot


class BotAppId(BaseModel):
    appid: str
    token: str = ''


class BotAccountModel(BotAppId):
    id: int = None
    private: int = 0
    is_main: int = 0
    is_start: int = 1
    adapter: str = 'tencent'
    console_channel: Optional[str] = None

    host: Optional[str] = None
    ws_port: Optional[int] = None
    http_port: Optional[int] = None
    client_secret: Optional[str] = None

    start: int = 0

    def get_data(self):
        data = {**self.dict()}
        del data['id']
        del data['start']

        return data


@app.controller
class Bot:
    @app.route(method='get')
    async def link(self):
        return app.response(message='验证成功')

    @app.route(method='get')
    async def get_all_bot(self):
        res = query_to_list(BotAccounts.select())

        for item in res:
            item['alive'] = 0
            item['running'] = 0

            if item['appid'] in bot:
                item['running'] = 1
                if bot[item['appid']].instance.alive:
                    item['alive'] = 1

        return app.response(data=res)

    @app.route()
    async def add_bot(self, data: BotAccountModel):
        if BotAccounts.get_or_none(appid=data.appid):
            return app.response(code=500, message='AppId 已存在')

        if data.adapter == 'websocket':
            if BotAccounts.get_or_none(adapter='websocket', ws_port=data.ws_port):
                return app.response(code=500, message='websocket 适配器的 ws 端口不能重复')

        BotAccounts.create(**data.get_data())

        if data.start:
            await self.run_bot(data)

        return app.response(message='添加成功' + (f'正在启动 AppId {data.appid}' if data.start else ''))

    @app.route()
    async def edit_bot(self, data: BotAccountModel):
        if BotAccounts.get_or_none(appid=data.appid):
            return app.response(code=500, message='AppId 已存在')

        if data.adapter == 'websocket':
            if BotAccounts.get_or_none(adapter='websocket', ws_port=data.ws_port):
                return app.response(code=500, message='websocket 适配器的 ws 端口不能重复')

        BotAccounts.update(**data.get_data()).where(BotAccounts.id == data.id).execute()

        if data.start:
            await self.run_bot(data)

        return app.response(message='保存成功' + (f'正在启动 AppId {data.appid}' if data.start else ''))

    @app.route()
    async def run_bot(self, data: BotAccountModel):
        if data.appid in bot:
            return app.response(code=500, message='Bot 已存在')

        conf = BotAccounts.build_conf(data)
        bot.append(AmiyaBot(**conf), launch_browser=True)

        return app.response(message=f'正在启动 AppId {data.appid}')

    @app.route()
    async def stop_bot(self, data: BotAppId):
        if data.appid not in bot:
            return app.response(code=500, message='Bot 不存在')

        del bot[data.appid]

        return app.response(message=f'已关闭 AppId {data.appid}')

    @app.route()
    async def delete_bot(self, data: BotAppId):
        await self.stop_bot(data)

        BotAccounts.delete().where(BotAccounts.appid == data.appid).execute()

        return app.response(message=f'已删除 AppId {data.appid}')
