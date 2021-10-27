from flask import Flask, request

from core.database.models import Pool, PoolSpOperator
from core.database.manager import select_for_paginate, model_to_dict, SearchParams

from ..response import response


def gacha_controller(app: Flask):
    @app.route('/pool/getPoolsByPages', methods=['POST'])
    def get_pools_by_pages():
        params = request.json
        search = SearchParams(
            params['search'],
            contains=params['search'].keys()
        )

        data, count = select_for_paginate(Pool,
                                          search,
                                          order_by=(Pool.pool_id.desc(),),
                                          page=params['page'],
                                          page_size=params['pageSize'])

        data = {item['pool_id']: item for item in data}

        sp_list = PoolSpOperator.select().where(
            PoolSpOperator.pool_id.in_(list(data.keys()))
        )

        for item in sp_list:
            item: PoolSpOperator
            if item.pool_id in data:
                if 'spList' not in data[item.pool_id]:
                    data[item.pool_id]['spList'] = []
            data[item.pool_id]['spList'].append(model_to_dict(item))

        return response({'count': count, 'data': [item for i, item in data.items()]})

    @app.route('/pool/addNewPool', methods=['POST'])
    def add_pool():
        params = request.json

        check = Pool.get_or_none(pool_name=params['pool_name'])
        if check:
            return response(message='卡池已存在')

        pool: Pool = Pool.create(
            pickup_4=params['pickup_4'],
            pickup_5=params['pickup_5'],
            pickup_6=params['pickup_6'],
            pickup_s=params['pickup_s'],
            limit_pool=params['limit_pool'],
            pool_name=params['pool_name']
        )

        sp = []
        for item in params['spList']:
            sp.append({
                'pool_id': pool.pool_id,
                'operator_name': item['operator_name'],
                'rarity': item['rarity'],
                'classes': item['classes'],
                'image': item['image']
            })

        PoolSpOperator.insert_many(sp).execute()

        return response(message='添加成功')

    @app.route('/pool/editPool', methods=['POST'])
    def edit_pool():
        params = request.json

        pool: Pool = Pool.get_or_none(pool_name=params['pool_name'])
        if not pool:
            return response(message='卡池不存在')

        Pool.update(
            pickup_4=params['pickup_4'],
            pickup_5=params['pickup_5'],
            pickup_6=params['pickup_6'],
            pickup_s=params['pickup_s'],
            limit_pool=params['limit_pool']
        ).where(
            Pool.pool_id == pool.pool_id
        ).execute()

        sp = []
        for item in params['spList']:
            sp.append({
                'pool_id': pool.pool_id,
                'operator_name': item['operator_name'],
                'rarity': item['rarity'],
                'classes': item['classes'],
                'image': item['image']
            })

        PoolSpOperator.delete().where(PoolSpOperator.pool_id == pool.pool_id).execute()
        PoolSpOperator.insert_many(sp).execute()

        return response(message='修改成功')

    @app.route('/pool/delPool', methods=['POST'])
    def del_pool():
        params = request.json

        pool: Pool = Pool.get_or_none(pool_name=params['pool_name'])
        if not pool:
            return response(message='卡池不存在')

        Pool.delete().where(Pool.pool_id == pool.pool_id).execute()
        PoolSpOperator.delete().where(PoolSpOperator.pool_id == pool.pool_id).execute()

        return response(message='删除成功')
