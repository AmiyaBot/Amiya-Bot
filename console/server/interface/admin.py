from flask import Flask, request

from core.util.common import random_code
from core.database.models import Admin, AdminTraceLog
from core.database.manager import select_for_paginate

from ..response import response
from .auth import super_user


def admin_controller(app: Flask):
    @app.route('/admin/getAdminsByPages', methods=['POST'])
    def get_admins_by_pages():
        params = request.json
        equal = {}
        contains = {}

        if params['search']:
            equal = {
                'active': params['search']['active']
            }
            contains = {
                'user_id': params['search']['user_id']
            }

        data, count = select_for_paginate(Admin,
                                          equal,
                                          contains,
                                          page=params['page'],
                                          page_size=params['pageSize'])

        if not super_user():
            for i in range(len(data)):
                data[i]['password'] = len(data[i]['password']) * '*'

        return response({'count': count, 'data': data})

    @app.route('/admin/getAdminTraceByPages', methods=['POST'])
    def get_admin_trace_by_pages():
        params = request.json
        equal = {}
        contains = {}

        if params['search']:
            contains = {
                'user_id': params['search']['user_id'],
                'interface': params['search']['interface']
            }

        data, count = select_for_paginate(AdminTraceLog,
                                          equal,
                                          contains,
                                          order_by=(AdminTraceLog.time.desc(),),
                                          page=params['page'],
                                          page_size=params['pageSize'])

        return response({'count': count, 'data': data})

    @app.route('/admin/setActive', methods=['POST'])
    @super_user
    def set_active():
        user_id = request.json['user_id']
        active = request.json['active']

        Admin.update(active=active).where(Admin.user_id == user_id).execute()

        return response(message='设置成功')

    @app.route('/admin/registerAdmin', methods=['POST'])
    @super_user
    def register_admin():
        user_id = request.json['user_id']

        password = random_code(10)
        Admin.create(user_id=user_id, password=password)

        return response(message=f'{user_id} 注册成功，初始密码 {password}')

    @app.route('/admin/delAdmin', methods=['POST'])
    @super_user
    def del_admin():
        user_id = request.json['user_id']

        Admin.delete().where(Admin.user_id == user_id).execute()
        AdminTraceLog.delete().where(AdminTraceLog.user_id == user_id).execute()

        return response(message='删除成功')
