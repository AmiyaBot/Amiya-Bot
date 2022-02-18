from core.network import response
from core.network.httpServer.auth import AuthManager
from core.database import SearchParams, select_for_paginate
from core.database.user import Admin, User as UserBase, query_to_list

from .model.user import UserTable, UserState, AddCoupon, EditPassword
from functions.user import UserInfo
from functions.arknights.gacha.gacha import UserGachaInfo


class User:
    @classmethod
    async def get_users_by_pages(cls, items: UserTable, auth=AuthManager.depends()):
        search = SearchParams(
            items.search,
            equal=['sign_in', 'black'],
            contains=['user_id']
        )

        data, count = select_for_paginate(UserBase,
                                          search,
                                          page=items.page,
                                          page_size=items.pageSize)

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

    @classmethod
    async def set_black_user(cls, items: UserState, auth=AuthManager.depends()):
        UserBase.update(black=items.black).where(UserBase.user_id == items.user_id).execute()
        return response(message='设置成功')

    @classmethod
    async def send_coupon(cls, items: AddCoupon, auth=AuthManager.depends()):
        value = int(items.value)

        query = UserGachaInfo.update(coupon=UserGachaInfo.coupon + value)
        if items.users:
            query = query.where(UserGachaInfo.user_id.in_(items.users))
        query.execute()

        return response(message='发放成功')

    @classmethod
    async def edit_password(cls, items: EditPassword, auth=AuthManager.depends()):
        user_id = auth.user_id
        password = items.password
        new_password = items.new_password

        admin = Admin.get_or_none(user_id=user_id, password=password)
        if admin:
            Admin.update(password=new_password).where(Admin.user_id == user_id).execute()
            return response(message='修改成功')
        else:
            return response(message='密码错误', code=0)
