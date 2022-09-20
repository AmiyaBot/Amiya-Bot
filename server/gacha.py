from typing import Optional
from amiyabot.database import select_for_paginate
from core import app, bot
from core.database.bot import Pool

from .__model__ import QueryData, BaseModel


class PoolModel(BaseModel):
    id: int = None
    pool_name: str
    pickup_6: Optional[str] = ''
    pickup_5: Optional[str] = ''
    pickup_4: Optional[str] = ''
    pickup_s: Optional[str] = ''
    limit_pool: int


@app.controller
class Gacha:
    @app.route()
    async def get_pool(self, data: QueryData):
        select = Pool.select().order_by(Pool.id.desc())

        if data.search:
            select = select.where(
                Pool.pool_name.contains(data.search) |
                Pool.pickup_6.contains(data.search) |
                Pool.pickup_5.contains(data.search) |
                Pool.pickup_4.contains(data.search) |
                Pool.pickup_s.contains(data.search)
            )

        return app.response(
            select_for_paginate(select,
                                page=data.currentPage,
                                page_size=data.pageSize)
        )

    @app.route()
    async def add_pool(self, data: PoolModel):
        if Pool.get_or_none(pool_name=data.pool_name):
            return app.response(code=500, message='卡池已存在')

        Pool.create(**data.dict())

        return app.response(message='添加成功')

    @app.route()
    async def update_pool(self, data: PoolModel):
        pool: Pool = Pool.get_or_none(pool_name=data.pool_name)

        if pool.id != data.id:
            return app.response(code=500, message='卡池已存在')

        Pool.update(**data.dict()).where(Pool.id == data.id).execute()

        return app.response(message='更新成功')

    @app.route()
    async def delete_pool(self, data: PoolModel):
        Pool.delete().where(Pool.id == data.id).execute()

        return app.response(message=f'删除成功')

    @app.route(method='get')
    async def sync_pool(self):
        sync_pool = getattr(bot.plugins['amiyabot-arknights-gacha'], 'sync_pool')
        res = await sync_pool(force=True)
        if res:
            return app.response(message=f'同步成功')
        return app.response(code=500, message=f'同步失败')
