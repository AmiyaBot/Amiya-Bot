import random
import string

from core.network import response
from core.network.httpServer.auth import AuthManager
from core.database import SearchParams, select_for_paginate
from core.database.user import Admin as AdminBase

from .model.admin import EditPassword, AdminModel, AdminTable, AdminState


def random_code(length):
    pool = string.digits + string.ascii_letters
    code = ''
    for i in range(length):
        code += random.choice(pool)
    return code


class Admin:
    @classmethod
    async def edit_password(cls, params: EditPassword, auth=AuthManager.depends()):
        user_id = auth.user_id
        password = params.password
        new_password = params.newPassword

        admin = AdminBase.get_or_none(user_id=user_id, password=password)
        if admin:
            AdminBase.update(password=new_password).where(AdminBase.user_id == user_id).execute()
            return response(message='修改成功')
        else:
            return response(message='密码错误', code=0)

    @classmethod
    async def get_admins_by_pages(cls, params: AdminTable, auth=AuthManager.depends()):
        search = SearchParams(
            params.search,
            equal=['active'],
            contains=['user_id']
        )

        data, count = select_for_paginate(AdminBase,
                                          search,
                                          page=params.page,
                                          page_size=params.pageSize)
        for i in range(len(data)):
            data[i]['password'] = len(data[i]['password']) * '*'

        return response({'count': count, 'data': data})

    @classmethod
    async def register_admin(cls, params: AdminModel, auth=AuthManager.depends()):
        password = random_code(10)
        AdminBase.create(user_id=params.user_id, password=password)

        return response(message='注册成功', data=password)

    @classmethod
    async def set_active(cls, params: AdminState, auth=AuthManager.depends()):
        AdminBase.update(active=params.active).where(AdminBase.user_id == params.user_id).execute()

        return response(message='设置成功')

    @classmethod
    async def del_admin(cls, params: AdminModel, auth=AuthManager.depends()):

        AdminBase.delete().where(AdminBase.user_id == params.user_id).execute()

        return response(message='删除成功')
