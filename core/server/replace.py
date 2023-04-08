import time

from amiyabot.database import select_for_paginate, query_to_list
from core import app, bot
from core.database.bot import TextReplace, TextReplaceSetting

from .__model__ import QueryData, BaseModel


class ReplaceModel(BaseModel):
    id: int = None
    origin: str
    replace: str
    is_global: int = None
    is_active: int = None


class ReplaceSettingModel(BaseModel):
    id: int = None
    text: str
    status: int


@app.controller
class Replace:
    @app.route()
    async def get_replace(self, data: QueryData):
        select = TextReplace.select().order_by(TextReplace.id.desc())

        if data.search:
            select = select.where(
                TextReplace.origin.contains(data.search) |
                TextReplace.replace.contains(data.search)
            )

        return app.response(
            select_for_paginate(select,
                                page=data.currentPage,
                                page_size=data.pageSize)
        )

    @app.route()
    async def add_replace(self, data: ReplaceModel):
        if TextReplace.get_or_none(origin=data.origin, replace=data.replace, is_global=1):
            return app.response(code=500, message='全局替换已存在')

        TextReplace.create(
            user_id='0',
            group_id='0',
            origin=data.origin,
            replace=data.replace,
            in_time=int(time.time()),
            is_global=1,
            is_active=1
        )

        return app.response(message='添加成功')

    @app.route()
    async def update_replace(self, data: ReplaceModel):
        TextReplace.update(**data.dict()).where(TextReplace.id == data.id).execute()

        return app.response(message='更新成功')

    @app.route()
    async def delete_replace(self, data: ReplaceModel):
        TextReplace.delete().where(TextReplace.id == data.id).execute()

        return app.response(message='删除成功')

    @app.route(method='get')
    async def get_replace_setting(self):
        return app.response(
            query_to_list(TextReplaceSetting.select())
        )

    @app.route()
    async def add_replace_setting(self, data: ReplaceSettingModel):
        if TextReplaceSetting.get_or_none(text=data.text):
            return app.response(code=500, message='标签已存在')

        TextReplaceSetting.create(
            text=data.text,
            status=data.status
        )

        return app.response(message='添加成功')

    @app.route()
    async def delete_replace_setting(self, data: ReplaceSettingModel):
        TextReplaceSetting.delete().where(TextReplaceSetting.id == data.id).execute()

        return app.response(message='删除成功')

    @app.route(method='get')
    async def sync_replace(self):
        if 'amiyabot-replace' not in bot.plugins:
            return app.response(code=500, message='尚未安装此插件')

        sync_replace = getattr(bot.plugins['amiyabot-replace'], 'sync_replace')
        res = await sync_replace(force=True)
        if res:
            return app.response(message=f'同步成功')
        return app.response(code=500, message=f'同步失败')

    @app.route(method='get', allow_unauthorized=True)
    async def get_global_replace(self):
        res = query_to_list(TextReplace.select().where(TextReplace.is_global == 1, TextReplace.is_active == 1))

        for item in res:
            item['user_id'] = '0'
            item['group_id'] = '0'

        return app.response(data=res)
