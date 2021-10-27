from flask import Flask, request

from core.database.models import GachaConfig
from core.database.manager import select_for_paginate, SearchParams
from dataSource import DataSource, Operator

from ..response import response


def operator_controller(app: Flask, data_source: DataSource):
    @app.route('/operator/getAllOperator', methods=['POST'])
    def get_all_operator():
        operators = []

        for name, item in data_source.operators.items():
            item: Operator
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

    @app.route('/operator/getOperatorGachaConfig', methods=['POST'])
    def get_operator_gacha_config():
        params = request.json
        search = SearchParams(
            params['search'],
            equal=['operator_type'],
            contains=['operator_name']
        )

        data, count = select_for_paginate(GachaConfig,
                                          search,
                                          order_by=(GachaConfig.conf_id.desc(),),
                                          page=params['page'],
                                          page_size=params['pageSize'])

        return response({'count': count, 'data': data})

    @app.route('/operator/addNewConfig', methods=['POST'])
    def add_config():
        params = request.json

        check = GachaConfig.get_or_none(operator_name=params['operator_name'])
        if check:
            return response(message='干员已存在')

        GachaConfig.create(
            operator_name=params['operator_name'],
            operator_type=params['operator_type']
        )

        return response(message='添加成功')

    @app.route('/operator/editConfig', methods=['POST'])
    def edit_config():
        params = request.json

        GachaConfig.update(
            operator_name=params['operator_name'],
            operator_type=params['operator_type']
        ).where(
            GachaConfig.conf_id == params['conf_id']
        ).execute()

        return response(message='修改成功')

    @app.route('/operator/delConfig', methods=['POST'])
    def del_config():
        params = request.json

        GachaConfig.delete().where(
            GachaConfig.conf_id == params['conf_id']
        ).execute()

        return response(message='删除成功')
