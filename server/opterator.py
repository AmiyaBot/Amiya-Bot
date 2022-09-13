from amiyabot.database import select_for_paginate, query_to_list
from core import app
from core.database.bot import OperatorIndex, OperatorConfig

from .__model__ import QueryData, BaseModel


class OperatorConfigModel(BaseModel):
    name: str
    operator_type: int


@app.controller
class Operator:
    @app.route(method='get')
    async def get_all_operator(self):
        return app.response(
            query_to_list(OperatorIndex.select())
        )

    @app.route()
    async def get_operator(self, data: QueryData):
        select = OperatorIndex.select(OperatorIndex, OperatorConfig) \
            .join(OperatorConfig, 'left join', on=(OperatorConfig.operator_name == OperatorIndex.name))

        if data.search:
            select = select.where(
                OperatorIndex.name.contains(data.search) |
                OperatorIndex.en_name.contains(data.search)
            )

        return app.response(
            select_for_paginate(select,
                                page=data.currentPage,
                                page_size=data.pageSize)
        )

    @app.route()
    async def set_operator(self, data: OperatorConfigModel):
        if OperatorConfig.get_or_none(operator_name=data.name):
            OperatorConfig.update(operator_type=data.operator_type).where(
                OperatorConfig.operator_name == data.name).execute()
        else:
            OperatorConfig.create(operator_name=data.name, operator_type=data.operator_type)

        return app.response(message='更新成功')
