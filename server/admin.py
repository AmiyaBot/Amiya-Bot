from amiyabot.database import select_for_paginate
from core import app
from core.database.bot import Admin as AdminAccount

from .__model__ import QueryData, BaseModel


class AdminModel(BaseModel):
    account: str
    remark: str = None


@app.controller
class Admin:
    @app.route()
    async def get_admin(self, data: QueryData):
        select = AdminAccount.select()

        if data.search:
            select = select.where(
                AdminAccount.account.contains(data.search) |
                AdminAccount.remark.contains(data.search)
            )

        return app.response(
            select_for_paginate(select,
                                page=data.currentPage,
                                page_size=data.pageSize)
        )

    @app.route()
    async def add_admin(self, data: AdminModel):
        if AdminAccount.get_or_none(account=data.account):
            return app.response(code=500, message='管理员已存在')

        AdminAccount.create(account=data.account, remark=data.remark)

        return app.response(message='添加成功')

    @app.route()
    async def delete_admin(self, data: AdminModel):
        AdminAccount.delete().where(AdminAccount.account == data.account).execute()

        return app.response(message=f'已删除管理员：{data.account}')
