from core.network import response
from core.network.httpServer.loader import interface
from core.network.httpServer.auth import AuthManager
from core.database import SearchParams, select_for_paginate, query_to_list
from core.database.bot import TextReplace, TextReplaceSetting

from .model.replace import ReplaceTable, DeleteReplace, ReplaceDataItem, ReplaceSettingItem


class Replace:
    @staticmethod
    @interface.register()
    async def get_replace_text_by_pages(params: ReplaceTable, auth=AuthManager.depends()):
        search = SearchParams(
            params.search,
            equal=['is_global', 'is_active'],
            contains=['user_id', 'group_id', 'origin', 'replace']
        )

        data, count = select_for_paginate(TextReplace,
                                          search,
                                          page=params.page,
                                          page_size=params.pageSize)

        return response({'count': count, 'data': data})

    @staticmethod
    @interface.register()
    async def delete_replace_text(params: DeleteReplace, auth=AuthManager.depends()):
        if params.group_origin_all:
            TextReplace.delete().where(TextReplace.group_id == params.group_id,
                                       TextReplace.origin == params.origin).execute()

        elif params.user_all:
            TextReplace.delete().where(TextReplace.group_id == params.group_id,
                                       TextReplace.user_id == params.user_id).execute()

        elif params.group_all:
            TextReplace.delete().where(TextReplace.group_id == params.group_id).execute()

        elif params.origin_all:
            TextReplace.delete().where(TextReplace.origin == params.origin).execute()

        elif params.replace_all:
            TextReplace.delete().where(TextReplace.replace == params.replace).execute()

        else:
            TextReplace.delete().where(TextReplace.id == params.id).execute()

        return response(message='删除成功')

    @staticmethod
    @interface.register()
    async def change_replace_text_status(params: ReplaceDataItem, auth=AuthManager.depends()):
        TextReplace \
            .update(is_global=params.is_global, is_active=params.is_active) \
            .where(TextReplace.id == params.id) \
            .execute()

        return response(message='设置成功')

    @staticmethod
    @interface.register()
    async def get_text_replace_setting(auth=AuthManager.depends()):
        return response(data=query_to_list(TextReplaceSetting.select()))

    @staticmethod
    @interface.register()
    async def add_replace_setting(params: ReplaceSettingItem, auth=AuthManager.depends()):

        data: TextReplaceSetting = TextReplaceSetting.create(text=params.text, status=params.status)

        return response(message='添加成功', data=data.id)

    @staticmethod
    @interface.register()
    async def delete_replace_setting(params: ReplaceSettingItem, auth=AuthManager.depends()):

        TextReplaceSetting.delete().where(TextReplaceSetting.id == params.id).execute()

        return response(message='删除成功')
