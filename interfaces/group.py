import re
import time
import asyncio

from typing import List
from core.database import SearchParams, select_for_paginate
from core.database.group import db as group, GroupActive, GroupSetting, GroupNotice, Group as GroupData
from core.database.messages import db as messages
from core.network import response
from core.network.httpServer.loader import interface
from core.network.httpServer.auth import AuthManager
from core import http, websocket, custom_chain, log

from .model.group import GroupInfo, GroupTable, GroupStatus, GroupNoticeTable, Notice


class Group:
    @staticmethod
    @interface.register()
    async def get_group_by_pages(params: GroupTable, auth=AuthManager.depends()):
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
            value = getattr(params.search, item)
            if value:
                where.append(f"{field} like '%{value}%'")

        for field, item in equal.items():
            value = getattr(params.search, item)
            if value:
                where.append(f"{field} = '{value}'")

        if params.search.orderBy:
            field = params.search.orderByField

            if field == 'group_id':
                order = f'order by g.group_id {params.search.orderBy}'
            elif field == 'group_name':
                order = f'order by g.group_name {params.search.orderBy}'
            elif field == 'message_num':
                order = f'order by g4.message_num {params.search.orderBy}'

        if where:
            where = 'where ' + ' and '.join(where)

        sql = re.sub(' +', ' ', f'''
        select g.group_id,
               g.group_name,
               g.permission,
               g2.active,
               g2.sleep_time,
               g3.send_notice,
               g3.send_weibo
        from `group` g
                 left join group_active g2 on g.group_id = g2.group_id
                 left join group_setting g3 on g.group_id = g3.group_id
                  {where if where else ''} {order if order else ''}
        '''.strip().replace('\n', ' '))

        fields = [
            'group_id',
            'group_name',
            'permission',
            'active',
            'sleep_time',
            'send_notice',
            'send_weibo'
        ]

        limit = (params.page - 1) * params.pageSize
        offset = params.page * params.pageSize

        res = group.execute_sql(sql).fetchall()
        res = [{fields[i]: n for i, n in enumerate(row)} for row in res]
        page = res[limit:offset]

        gid = ', '.join([n['group_id'] for n in page])
        if gid:
            msg = messages.execute_sql(
                f'select group_id, count(*) from message_record where group_id in ({gid}) group by group_id'
            ).fetchall()
            msg = {str(n[0]): n[1] for n in msg}

            for item in page:
                item['message_num'] = 0
                if item['group_id'] in msg:
                    item['message_num'] = msg[item['group_id']]

        return response({'count': len(res), 'data': page})

    @staticmethod
    @interface.register()
    async def refresh_group_list(auth=AuthManager.depends()):
        group_list = await http.get_group_list()

        GroupData.truncate_table()
        GroupData.batch_insert(group_list)

        return response(message=f'同步完成，共 {len(group_list)} 个群。')

    @staticmethod
    @interface.register()
    async def get_member_list(auth=AuthManager.depends()):
        return response(code=0, message='接口未开放')

    @staticmethod
    @interface.register()
    async def change_group_status(params: GroupStatus, auth=AuthManager.depends()):
        if params.active is not None:
            GroupActive.insert_or_update(
                insert={
                    'group_id': params.group_id,
                    'active': params.active
                },
                update={
                    GroupActive.active: params.active
                },
                conflict_target=[GroupActive.group_id]
            )
        else:
            for name in ['send_notice', 'send_weibo']:
                value = getattr(params, name)
                if name is not None:
                    GroupSetting.insert_or_update(
                        insert={
                            name: value,
                            'group_id': params.group_id
                        },
                        update={
                            getattr(GroupSetting, name): value
                        },
                        conflict_target=[GroupSetting.group_id]
                    )

        return response(message='修改成功')

    @staticmethod
    @interface.register()
    async def leave_group(params: GroupInfo, auth=AuthManager.depends()):
        members = await http.leave_group(params.group_id)
        return response(members)

    @staticmethod
    @interface.register()
    async def get_group_notice_by_pages(params: GroupNoticeTable, auth=AuthManager.depends()):
        search = SearchParams(
            params.search,
            contains=['content', 'send_user']
        )

        data, count = select_for_paginate(GroupNotice,
                                          search,
                                          page=params.page,
                                          page_size=params.pageSize)

        return response({'count': count, 'data': data})

    @staticmethod
    @interface.register()
    async def push_notice(params: Notice, auth=AuthManager.depends()):
        group_list = await http.get_group_list()

        disabled: List[GroupSetting] = GroupSetting.select().where(GroupSetting.send_notice == 0)
        disabled: List[str] = [n.group_id for n in disabled]

        success = 0
        for item in group_list:
            group_id = item['group_id']
            group_name = item['group_name']

            if str(group_id) in disabled:
                continue

            async with log.catch('push error:'):
                data = custom_chain(group_id=int(group_id))
                data.text(f'亲爱的{group_name}的博士们，有来自管理员{auth.user_id}的公告：\n\n{params.content}')

                await websocket.send_message(data)

                success += 1

            await asyncio.sleep(0.5)

        GroupNotice.create(
            content=params.content,
            send_time=int(time.time()),
            send_user=auth.user_id
        )

        return response(message=f'公告推送完毕，成功：{success}/{len(group_list)}')

    @staticmethod
    @interface.register()
    async def del_notice(params: Notice, auth=AuthManager.depends()):
        GroupNotice.delete().where(GroupNotice.notice_id == params.notice_id).execute()
        return response(message='删除成功')
