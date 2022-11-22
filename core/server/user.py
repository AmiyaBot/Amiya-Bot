from amiyabot.database import select_for_paginate
from core import app
from core.database.user import User as UserTable, UserInfo, UserGachaInfo

from .__model__ import QueryData, BaseModel


class UserModel(BaseModel):
    user_id: str
    coupon: int
    jade_point: int
    black: int


@app.controller
class User:
    @app.route()
    async def get_user(self, data: QueryData):
        select = UserTable.select(UserTable, UserInfo, UserGachaInfo) \
            .join(UserInfo, 'left join', on=(UserInfo.user_id == UserTable.user_id)) \
            .join(UserGachaInfo, 'left join', on=(UserGachaInfo.user_id == UserTable.user_id))

        if data.search:
            select = select.where(
                UserTable.user_id.contains(data.search) |
                UserTable.nickname.contains(data.search)
            )

        return app.response(
            select_for_paginate(select,
                                page=data.currentPage,
                                page_size=data.pageSize)
        )

    @app.route()
    async def edit_user(self, data: UserModel):
        UserTable.update(black=data.black).where(UserTable.user_id == data.user_id).execute()
        UserInfo.update(jade_point=data.jade_point).where(UserInfo.user_id == data.user_id).execute()
        UserGachaInfo.update(coupon=data.coupon).where(UserGachaInfo.user_id == data.user_id).execute()

        return app.response(message='修改成功')
