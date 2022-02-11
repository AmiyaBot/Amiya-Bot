from core.network import response
from core.network.httpServer.auth import AuthManager
from core.database import SearchParams, select_for_paginate, query_to_list

from .model.replace import ReplaceTable, DeleteReplace, ReplaceDataItem, ReplaceSettingItem
from functions.replace import TextReplace, TextReplaceSetting


class Replace:
    @classmethod
    async def get_replace_text_by_pages(cls, items: ReplaceTable, auth=AuthManager.depends()):
        search = SearchParams(
            items.search,
            equal=['is_global', 'is_active'],
            contains=['user_id', 'group_id', 'origin', 'replace']
        )

        data, count = select_for_paginate(TextReplace,
                                          search,
                                          page=items.page,
                                          page_size=items.pageSize)

        return response({'count': count, 'data': data})

    @classmethod
    async def delete_replace_text(cls, items: DeleteReplace, auth=AuthManager.depends()):
        if items.group_origin_all:
            TextReplace.delete().where(TextReplace.group_id == items.group_id,
                                       TextReplace.origin == items.origin).execute()

        elif items.user_all:
            TextReplace.delete().where(TextReplace.group_id == items.group_id,
                                       TextReplace.user_id == items.user_id).execute()

        elif items.group_all:
            TextReplace.delete().where(TextReplace.group_id == items.group_id).execute()

        elif items.origin_all:
            TextReplace.delete().where(TextReplace.origin == items.origin).execute()

        elif items.replace_all:
            TextReplace.delete().where(TextReplace.replace == items.replace).execute()

        else:
            TextReplace.delete().where(TextReplace.id == items.id).execute()

        return response(message='删除成功')

    @classmethod
    async def change_replace_text_status(cls, items: ReplaceDataItem, auth=AuthManager.depends()):
        TextReplace \
            .update(is_global=items.is_global, is_active=items.is_active) \
            .where(TextReplace.id == items.id) \
            .execute()

        return response(message='设置成功')

    @classmethod
    async def get_text_replace_setting(cls, auth=AuthManager.depends()):
        return response(data=query_to_list(TextReplaceSetting.select()))

    @classmethod
    async def add_replace_setting(cls, items: ReplaceSettingItem, auth=AuthManager.depends()):

        data: TextReplaceSetting = TextReplaceSetting.create(text=items.text, status=items.status)

        return response(message='添加成功', data=data.id)

    @classmethod
    async def delete_replace_setting(cls, items: ReplaceSettingItem, auth=AuthManager.depends()):

        TextReplaceSetting.delete().where(TextReplaceSetting.id == items.id).execute()

        return response(message='删除成功')
