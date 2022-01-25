import time
import asyncio

from typing import List
from core.database import SearchParams, select_for_paginate
from core.database.group import db, GroupActive, GroupSetting, GroupNotice, Group as GroupData
from core.network import response
from core.network.httpServer.auth import AuthManager
from core import http, websocket, custom_chain, log

from .model.group import GroupInfo, GroupTable, GroupStatus, GroupNoticeTable, Notice


class Group:
    @classmethod
    async def get_group_by_pages(cls, items: GroupTable, auth=AuthManager.depends()):
        where = []
        order = ''

        like = {
            'g.group_id': 'group_id',
            'g.group_name': 'group_name'
        }
        equal = {
            'g.permission': 'permission',
            'g2.active': 'active',
            'g3.send_notice': 'send_notice',
            'g3.send_weibo': 'send_weibo'
        }

        for field, item in like.items():
            value = getattr(items.search, item)
            if value:
                where.append(f"{field} like '%{value}%'")

        for field, item in equal.items():
            value = getattr(items.search, item)
            if value:
                where.append(f"{field} = '{value}'")

        if items.search.orderBy:
            field = items.search.orderByField

            if field == 'group_id':
                order = f'order by g.group_id {items.search.orderBy}'
            elif field == 'group_name':
                order = f'order by g.group_name {items.search.orderBy}'
            elif field == 'message_num':
                order = f'order by g4.message_num {items.search.orderBy}'

        if where:
            where = 'where ' + ' and '.join(where)

        sql = f'''
        select g.group_id,
               g.group_name,
               g.permission,
               g2.active,
               g2.sleep_time,
               g3.send_notice,
               g3.send_weibo
        from "group" g
                 left join group_active g2 on g.group_id = g2.group_id
                 left join group_setting g3 on g.group_id = g3.group_id
                  {where if where else ''} {order if order else ''}
        '''.strip().replace('\n', ' ')

        fields = [
            'group_id',
            'group_name',
            'permission',
            'active',
            'sleep_time',
            'send_notice',
            'send_weibo'
        ]

        limit = (items.page - 1) * items.pageSize
        offset = items.page * items.pageSize

        res = db.execute_sql(sql).fetchall()
        res = [{fields[i]: n for i, n in enumerate(row)} for row in res]

        return response({'count': len(res), 'data': res[limit:offset]})

    @classmethod
    async def refresh_group_list(cls, auth=AuthManager.depends()):
        group_list = await http.get_group_list()

        GroupData.truncate_table()
        GroupData.insert_many(group_list).execute()

        return response(message=f'同步完成，共 {len(group_list)} 个群。')

    @classmethod
    async def get_member_list(cls, auth=AuthManager.depends()):
        return response(code=0, message='接口未开放')

    @classmethod
    async def change_group_status(cls, items: GroupStatus, auth=AuthManager.depends()):
        if items.active is not None:
            GroupActive.insert(group_id=items.group_id, active=items.active).on_conflict(
                conflict_target=[GroupActive.group_id],
                update={
                    GroupActive.active: items.active
                }
            ).execute()
        else:
            for name in ['send_notice', 'send_weibo']:
                value = getattr(items, name)
                if name is not None:
                    GroupSetting.insert(**{name: value, 'group_id': items.group_id}).on_conflict(
                        conflict_target=[GroupSetting.group_id],
                        update={
                            getattr(GroupSetting, name): value
                        }
                    ).execute()

        return response(message='修改成功')

    @classmethod
    async def leave_group(cls, items: GroupInfo, auth=AuthManager.depends()):
        members = await http.leave_group(items.group_id)
        return response(members)

    @classmethod
    async def get_group_notice_by_pages(cls, items: GroupNoticeTable, auth=AuthManager.depends()):
        search = SearchParams(
            items.search,
            contains=['content', 'send_user']
        )

        data, count = select_for_paginate(GroupNotice,
                                          search,
                                          page=items.page,
                                          page_size=items.pageSize)

        return response({'count': count, 'data': data})

    @classmethod
    async def push_notice(cls, items: Notice, auth=AuthManager.depends()):
        groups: List[GroupSetting] = GroupSetting.select().where(GroupSetting.send_notice == 1)
        group_name = {
            item.group_id: item.group_name
            for item in GroupData.select().where(GroupData.group_id.in_([item.group_id for item in groups]))
        }

        success = 0
        for item in groups:
            async with log.catch('push error:'):
                data = custom_chain(group_id=int(item.group_id))
                data.text(f'亲爱的{group_name[item.group_id]}的博士们，有来自管理员{auth.user_id}的公告：\n\n{items.content}')

                await websocket.send(data)

                success += 1

            await asyncio.sleep(0.5)

        GroupNotice.create(
            content=items.content,
            send_time=int(time.time()),
            send_user=auth.user_id
        )

        return response(message=f'公告推送完毕，成功：{success}/{len(groups)}')

    @classmethod
    async def del_notice(cls, items: Notice, auth=AuthManager.depends()):
        GroupNotice.delete().where(GroupNotice.notice_id == items.notice_id).execute()
        return response(message='删除成功')
