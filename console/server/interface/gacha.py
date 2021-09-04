from flask import Flask, request

from core.database.models import Pool
from core.database.manager import select_for_paginate

from ..response import response


def gacha_controller(app: Flask):
    @app.route('/pool/getPoolsByPages', methods=['POST'])
    def get_pools_by_pages():
        params = request.json

        data, count = select_for_paginate(Pool,
                                          params['search'],
                                          order_by=(Pool.pool_id.desc(),),
                                          page=params['page'],
                                          page_size=params['pageSize'])

        return response({'count': count, 'data': data})

    @app.route('/pool/addNewPool', methods=['POST'])
    def add_pool():
        params = request.json

        check = Pool.get_or_none(pool_name=params['pool_name'])
        if check:
            return response(message='卡池已存在')

        Pool.create(
            pickup_4=params['pickup_4'],
            pickup_5=params['pickup_5'],
            pickup_6=params['pickup_6'],
            pickup_s=params['pickup_s'],
            limit_pool=params['limit_pool'],
            pool_name=params['pool_name']
        )

        return response(message='添加成功')

    @app.route('/pool/editPool', methods=['POST'])
    def edit_pool():
        params = request.json

        Pool.update(
            pickup_4=params['pickup_4'],
            pickup_5=params['pickup_5'],
            pickup_6=params['pickup_6'],
            pickup_s=params['pickup_s'],
            limit_pool=params['limit_pool']
        ).where(
            Pool.pool_name == params['pool_name']
        ).execute()

        return response(message='修改成功')

    @app.route('/pool/delPool', methods=['POST'])
    def del_pool():
        params = request.json

        Pool.delete().where(
            Pool.pool_name == params['pool_name']
        ).execute()

        return response(message='删除成功')
