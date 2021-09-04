import time

from flask import Flask, session, request

from core.database.models import Admin

from ..response import response


def auth_controller(app: Flask):
    @app.before_request
    def verify_access():
        url = request.path
        if not url.startswith('/static') and url not in ['/', '/login']:
            if not session.get('user'):
                return response(code=400, message='登录失效')

    @app.route('/login', methods=['POST'])
    def login():
        user_id = request.json['userId']
        password = request.json['password']

        admin: Admin = Admin.get_or_none(user_id=user_id)

        if admin is None:
            return response(code=0, message='用户不存在')

        if admin.active == 0:
            return response(code=0, message='用户已被禁用')

        if admin.password != password:
            return response(code=0, message='密码错误')

        session.permanent = True
        session['user'] = user_id

        Admin \
            .update(last_login=int(time.time()), last_login_ip=request.remote_addr) \
            .where(Admin.user_id == user_id) \
            .execute()

        return response(message='登录成功')

    @app.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        return response(message='退出登录成功')
