from flask import Flask, request

from core.database.models import User
from core.database.manager import select_for_paginate

from ..response import response


def user_controller(app: Flask):
    @app.route('/user/getUsersByPages', methods=['POST'])
    def get_users_by_pages():
        params = request.json
        equal = {}
        contains = {}

        if params['search']:
            equal = {
                'sign_in': params['search']['sign_in'],
                'black': params['search']['black']
            }
            contains = {
                'user_id': params['search']['user_id']
            }

        data, count = select_for_paginate(User,
                                          equal,
                                          contains,
                                          order_by=(User.sign_in.desc(), User.user_feeling.desc()),
                                          page=params['page'],
                                          page_size=params['pageSize'])

        return response({'count': count, 'data': data})

    @app.route('/user/setBlackUser', methods=['POST'])
    def set_black_user():
        params = request.json

        User.update(black=params['black']).where(User.user_id == params['user_id']).execute()

        return response(message='设置成功')

    @app.route('/user/sendCoupon', methods=['POST'])
    def send_coupon():
        params = request.json

        value = int(params['value'])

        query = User.update(coupon=User.coupon + value)
        if params['users']:
            query = query.where(User.user_id.in_(params['users']))
        query.execute()

        return response(message='发放成功')
