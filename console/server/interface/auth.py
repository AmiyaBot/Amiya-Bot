import time
import json

from functools import wraps
from flask import Flask, session, request

from core import AmiyaBot
from core.util.config import config
from core.database.models import Admin, AdminTraceLog

from ..response import response


def super_user(func=None):
    admin = str(config.account.admin)
    if func is None:
        return str(session.get('user')) == admin

    @wraps(func)
    def check():
        if str(session.get('user')) != admin:
            return response(code=0, message='您没有此接口的操作权限')
        return func()

    return check


def auth_controller(app: Flask, bot: AmiyaBot):
    @app.before_request
    def verify_access():
        url = request.path
        user = session.get('user')
        methods = request.method
        params = json.dumps(request.json, ensure_ascii=False)
        static = url.startswith('/static')

        if not static and url not in ['/', '/login']:
            if not user:
                return response(code=400, message='登录失效')

            admin: Admin = Admin.get_or_none(user_id=user)
            if not admin or admin.active == 0:
                session.clear()
                return response(code=400, message='您已被强制退出')

        if not static and user and url not in ['/editPassword']:
            AdminTraceLog.create(
                user_id=user,
                interface=url,
                methods=methods,
                params=params,
                time=int(time.time()),
            )

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

    @app.route('/editPassword', methods=['POST'])
    def edit_password():
        user_id = session.get('user')
        password = request.json['password']
        new_password = request.json['newPassword']

        admin = Admin.get_or_none(user_id=user_id, password=password)
        if admin:
            Admin.update(password=new_password).where(Admin.user_id == user_id).execute()
            return response(message='修改成功')
        else:
            return response(message='密码错误', code=0)

    @app.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        return response(message='退出登录成功')

    @app.route('/restart', methods=['POST'])
    def restart():
        bot.restart()
        return response(code=300, message='即将进入重启，重启需要一定时间，请耐心等待...')
