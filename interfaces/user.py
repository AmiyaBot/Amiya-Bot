from core.network import response
from core.network.httpServer.loader import interface
from core.network.httpServer.auth import AuthManager
from core.database import SearchParams, select_for_paginate
from core.database.user import User as UserBase, UserInfo, UserGachaInfo, query_to_list

from .model.user import UserTable, UserState, AddCoupon


class User:
    @staticmethod
    @interface.register()
    async def get_users_by_pages(params: UserTable, auth=AuthManager.depends()):
        search = SearchParams(
            params.search,
            equal=['sign_in', 'black'],
            contains=['user_id']
        )

        data, count = select_for_paginate(UserBase,
                                          search,
                                          page=params.page,
                                          page_size=params.pageSize)

        user_id = [n['user_id'] for n in data]

        user_info_map = {
            n['user_id']['user_id']: n for n in query_to_list(UserInfo.select().where(UserInfo.user_id.in_(user_id)))
        }
        user_gacha_info_map = {
            n['user_id']['user_id']: n for n in
            query_to_list(UserGachaInfo.select().where(UserGachaInfo.user_id.in_(user_id)))
        }

        for item in data:
            user_id = item['user_id']
            if user_id in user_info_map:
                item.update(user_info_map[user_id])
            if user_id in user_gacha_info_map:
                item.update(user_gacha_info_map[user_id])

        return response({'count': count, 'data': data})

    @staticmethod
    @interface.register()
    async def set_black_user(params: UserState, auth=AuthManager.depends()):
        UserBase.update(black=params.black).where(UserBase.user_id == params.user_id).execute()
        return response(message='设置成功')

    @staticmethod
    @interface.register()
    async def send_coupon(params: AddCoupon, auth=AuthManager.depends()):
        value = int(params.value)

        query = UserGachaInfo.update(coupon=UserGachaInfo.coupon + value)
        if params.users:
            query = query.where(UserGachaInfo.user_id.in_(params.users))
        query.execute()

        return response(message='发放成功')
