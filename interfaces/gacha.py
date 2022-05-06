from typing import List
from fastapi import File, UploadFile

from core.util import create_dir
from core.network import response
from core.network.httpServer.loader import interface
from core.network.httpServer.auth import AuthManager
from core.database import SearchParams, select_for_paginate, model_to_dict, query_to_list
from core.database.bot import Pool as PoolBase, PoolSpOperator, GachaConfig
from core.resource.arknightsGameData import ArknightsGameData

from .model.pool import PoolTable, PoolInfo, GachaConfigTable, GachaConfigItem


class Pool:
    @staticmethod
    @interface.register()
    async def get_pools_by_pages(params: PoolTable, auth=AuthManager.depends()):
        search = SearchParams(
            params.search,
            contains=['limit_pool', 'pool_name']
        )

        data, count = select_for_paginate(PoolBase,
                                          search,
                                          order_by=(PoolBase.id.desc(),),
                                          page=params.page,
                                          page_size=params.pageSize)

        data = {item['id']: item for item in data}

        sp_list: List[PoolSpOperator] = PoolSpOperator.select().where(
            PoolSpOperator.pool_id.in_(list(data.keys()))
        )

        for item in sp_list:
            _id = item.pool_id.id
            if _id in data and 'sp_list' not in data[_id]:
                data[_id]['sp_list'] = []
            data[_id]['sp_list'].append(model_to_dict(item))

        return response({'count': count, 'data': [item for i, item in data.items()]})

    @staticmethod
    @interface.register()
    async def add_new_pool(params: PoolInfo, auth=AuthManager.depends()):
        check = PoolBase.get_or_none(pool_name=params.pool_name)
        if check:
            return response(message='卡池已存在')

        pool: PoolBase = PoolBase.create(
            pickup_4=params.pickup_4,
            pickup_5=params.pickup_5,
            pickup_6=params.pickup_6,
            pickup_s=params.pickup_s,
            limit_pool=params.limit_pool,
            pool_name=params.pool_name
        )

        sp = []
        for item in params.sp_list:
            sp.append({
                'pool_id': pool.id,
                'operator_name': item.operator_name,
                'rarity': item.rarity,
                'classes': item.classes,
                'image': item.image
            })

        PoolSpOperator.batch_insert(sp)

        return response(message='添加成功')

    @staticmethod
    @interface.register()
    async def edit_pool(params: PoolInfo, auth=AuthManager.depends()):
        pool: PoolBase = PoolBase.get_or_none(pool_name=params.pool_name)
        if not pool:
            return response(message='卡池不存在')

        PoolBase.update(
            pickup_4=params.pickup_4,
            pickup_5=params.pickup_5,
            pickup_6=params.pickup_6,
            pickup_s=params.pickup_s,
            limit_pool=params.limit_pool
        ).where(
            PoolBase.id == pool.id
        ).execute()

        sp = []
        for item in params.sp_list:
            sp.append({
                'pool_id': pool.id,
                'operator_name': item.operator_name,
                'rarity': item.rarity,
                'classes': item.classes,
                'image': item.image
            })

        PoolSpOperator.delete().where(PoolSpOperator.pool_id == pool.id).execute()
        PoolSpOperator.batch_insert(sp)

        return response(message='修改成功')

    @staticmethod
    @interface.register()
    async def del_pool(params: PoolInfo, auth=AuthManager.depends()):
        pool: PoolBase = PoolBase.get_or_none(pool_name=params.pool_name)
        if not pool:
            return response(message='卡池不存在')

        PoolBase.delete().where(PoolBase.id == pool.id).execute()

        return response(message='删除成功')

    @staticmethod
    @interface.register()
    async def upload_image(file: UploadFile = File(...), auth=AuthManager.depends()):
        content = await file.read()
        path = 'resource/images/temp'

        create_dir(path)

        with open(f'{path}/{file.filename}', mode='wb') as f:
            f.write(content)

        return response(data={'filename': file.filename}, message='上传成功')

    @staticmethod
    @interface.register(method='get')
    async def get_gacha_pool():
        data = {
            'Pool': query_to_list(PoolBase.select()),
            'PoolSpOperator': query_to_list(PoolSpOperator.select()),
            'GachaConfig': query_to_list(GachaConfig.select())
        }

        for item in data['PoolSpOperator']:
            item['pool_id'] = item['pool_id']['id']

        return response(data=data)


class Operator:
    @staticmethod
    @interface.register()
    async def get_all_operator(auth=AuthManager.depends()):
        operators = []

        for name, item in ArknightsGameData().operators.items():
            operators.append(
                {
                    'name': name,
                    'en_name': item.en_name,
                    'class': item.classes,
                    'classes_sub': item.classes_sub,
                    'rarity': item.rarity
                }
            )

        return response(operators)

    @staticmethod
    @interface.register()
    async def get_operator_gacha_config(params: GachaConfigTable, auth=AuthManager.depends()):
        search = SearchParams(
            params.search,
            equal=['operator_type'],
            contains=['operator_name']
        )

        data, count = select_for_paginate(GachaConfig,
                                          search,
                                          order_by=(GachaConfig.id.desc(),),
                                          page=params.page,
                                          page_size=params.pageSize)

        return response({'count': count, 'data': data})

    @staticmethod
    @interface.register()
    async def add_config(params: GachaConfigItem, auth=AuthManager.depends()):
        check = GachaConfig.get_or_none(operator_name=params.operator_name)
        if check:
            return response(message='干员已存在')

        GachaConfig.create(
            operator_name=params.operator_name,
            operator_type=params.operator_type
        )

        return response(message='添加成功')

    @staticmethod
    @interface.register()
    async def edit_config(params: GachaConfigItem, auth=AuthManager.depends()):
        GachaConfig.update(
            operator_name=params.operator_name,
            operator_type=params.operator_type
        ).where(
            GachaConfig.id == params.id
        ).execute()

        return response(message='修改成功')

    @staticmethod
    @interface.register()
    async def del_config(params: GachaConfigItem, auth=AuthManager.depends()):
        GachaConfig.delete().where(
            GachaConfig.id == params.id
        ).execute()

        return response(message='删除成功')
