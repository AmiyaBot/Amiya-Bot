from flask import Flask, request

from core.database.models import User
from core.database.manager import select_for_paginate, SearchParams

from ..response import response
from .auth import super_user


def user_controller(app: Flask):
    @app.route('/user/getUsersByPages', methods=['POST'])
    def get_users_by_pages():
        params = request.json
        search = SearchParams(
            params['search'],
            equal=['sign_in', 'black'],
            contains=['user_id']
        )
        sort = None

        if params['search'] and '_sort' in params['search']:
            order_by = 'desc' if params['search']['_sort']['order'] == 'descending' else 'asc'
            field = params['search']['_sort']['field']
            sort = (getattr(getattr(User, field), order_by)(),)

        data, count = select_for_paginate(User,
                                          search,
                                          order_by=sort,
                                          page=params['page'],
                                          page_size=params['pageSize'])

        return response({'count': count, 'data': data})

    @app.route('/user/setBlackUser', methods=['POST'])
    def set_black_user():
        params = request.json

        User.update(black=params['black']).where(User.user_id == params['user_id']).execute()

        return response(message='设置成功')

    @app.route('/user/sendCoupon', methods=['POST'])
    @super_user
    def send_coupon():
        params = request.json

        value = int(params['value'])

        query = User.update(coupon=User.coupon + value)
        if params['users']:
            query = query.where(User.user_id.in_(params['users']))
        query.execute()

        return response(message='发放成功')
