import random
import string

from core.network import response
from core.network.httpServer.loader import interface
from core.network.httpServer.auth import AuthManager
from core.database import SearchParams, select_for_paginate, query_to_list
from core.database.user import Admin as AdminBase, Role as RoleBase

from .model.admin import *


def random_code(length):
    pool = string.digits + string.ascii_letters
    code = ''
    for i in range(length):
        code += random.choice(pool)
    return code


class Admin:
    @staticmethod
    @interface.register()
    async def edit_password(params: EditPassword, auth=AuthManager.depends()):
        user_id = auth.user_id
        password = params.password
        new_password = params.newPassword

        admin = AdminBase.get_or_none(user_id=user_id, password=password)
        if admin:
            AdminBase.update(password=new_password).where(AdminBase.user_id == user_id).execute()
            return response(message='修改成功')
        else:
            return response(message='密码错误', code=0)

    @staticmethod
    @interface.register()
    async def get_admins_by_pages(params: AdminTable, auth=AuthManager.depends()):
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
            data[i]['role_id'] = data[i]['role_id']['id'] if data[i]['role_id'] else 0

        return response({'count': count, 'data': data})

    @staticmethod
    @interface.register()
    async def register_admin(params: AdminModel, auth=AuthManager.depends()):
        password = random_code(10)
        AdminBase.create(user_id=params.user_id, password=password)

        return response(message='注册成功', data=password)

    @staticmethod
    @interface.register()
    async def set_active(params: AdminState, auth=AuthManager.depends()):
        AdminBase.update(active=params.active).where(AdminBase.user_id == params.user_id).execute()

        return response(message='设置成功')

    @staticmethod
    @interface.register()
    async def set_role(params: AdminRole, auth=AuthManager.depends()):
        AdminBase.update(role_id=params.role_id).where(AdminBase.user_id == params.user_id).execute()

        return response(message='设置成功')

    @staticmethod
    @interface.register()
    async def del_admin(params: AdminModel, auth=AuthManager.depends()):
        AdminBase.delete().where(AdminBase.user_id == params.user_id).execute()

        return response(message='删除成功')


class Role:
    @staticmethod
    @interface.register()
    async def get_roles_by_pages(params: RoleTable, auth=AuthManager.depends()):
        search = SearchParams(
            params.search,
            equal=['active'],
            contains=['role_name']
        )

        data, count = select_for_paginate(RoleBase,
                                          search,
                                          page=params.page,
                                          page_size=params.pageSize)

        return response({'count': count, 'data': data})

    @staticmethod
    @interface.register()
    async def get_all_roles(auth=AuthManager.depends()):
        return response(data=query_to_list(RoleBase.select()))

    @staticmethod
    @interface.register()
    async def set_active(params: RoleState, auth=AuthManager.depends()):
        if params.role_id == 1:
            return response(code=500, message='无法操作超级管理员')

        RoleBase.update(active=params.active).where(RoleBase.id == params.role_id).execute()

        return response(message='设置成功')

    @staticmethod
    @interface.register()
    async def del_role(params: RoleModel, auth=AuthManager.depends()):
        if params.id == 1:
            return response(code=500, message='无法操作超级管理员')

        RoleBase.delete().where(RoleBase.id == params.id).execute()
        AdminBase.update(role_id=None).where(AdminBase.role_id == params.id).execute()
        return response(message='删除成功')

    @staticmethod
    @interface.register()
    async def save_role(params: RoleModel, auth=AuthManager.depends()):
        data = {
            'role_name': params.role_name,
            'access_path': params.access_path,
        }
        if params.id:
            RoleBase.update(**data).where(RoleBase.id == params.id).execute()
        else:
            RoleBase.create(**data)

        return response(message='保存成功')
