import time
import threading

from flask import Flask, session, request

from core import AmiyaBot
from core.database.models import sqlite_db, Group, GroupActive, GroupSetting, GroupNotice
from core.database.manager import select_for_paginate, SearchParams

from ..response import response
from .auth import super_user


def group_controller(app: Flask, bot: AmiyaBot):
    @app.route('/group/getGroupByPages', methods=['POST'])
    def get_group_by_pages():
        params = request.json
        where = []
        order = ''
        if params['search']:

            like = {'g.group_id': 'group_id', 'g.group_name': 'group_name'}
            equal = {
                'g.permission': 'permission',
                'g2.active': 'active',
                'g3.send_notice': 'send_notice',
                'g3.send_weibo': 'send_weibo'
            }

            for field, item in like.items():
                if params['search'][item]:
                    where.append(f"{field} like '%{params['search'][item]}%'")

            for field, item in equal.items():
                if params['search'][item]:
                    where.append(f"{field} = '{params['search'][item]}'")

            if '_sort' in params['search'] and params['search']['_sort']['order']:
                order_by = 'desc' if params['search']['_sort']['order'] == 'descending' else 'asc'
                field = params['search']['_sort']['field']

                if field == 'group_id':
                    order = f'order by g.group_id {order_by}'
                if field == 'group_name':
                    order = f'order by g.group_name {order_by}'
                if field == 'message_num':
                    order = f'order by g4.message_num {order_by}'

        if where:
            where = 'where ' + ' and '.join(where)

        sql = f'''
        select g.group_id,
               g.group_name,
               g.permission,
               g2.active,
               g2.sleep_time,
               g3.send_notice,
               g3.send_weibo,
               g4.message_num
        from "group" g
                 left join groupactive g2 on g.group_id = g2.group_id
                 left join groupsetting g3 on g.group_id = g3.group_id
                 left join (select count(*) message_num, group_id from message where record = 'call' group by group_id)
                           g4 on g.group_id = g4.group_id {where if where else ''} {order if order else ''}
        '''

        fields = [
            'group_id',
            'group_name',
            'permission',
            'active',
            'sleep_time',
            'send_notice',
            'send_weibo',
            'message_num'
        ]
        res = sqlite_db.execute_sql(sql).fetchall()
        res = [{fields[i]: n for i, n in enumerate(row)} for row in res]

        limit = (params['page'] - 1) * params['pageSize']
        offset = params['page'] * params['pageSize']

        return response({'count': len(res), 'data': res[limit:offset]})

    @app.route('/group/refreshGroupList', methods=['POST'])
    def refresh_group_list():
        groups = bot.http.get_group_list()

        Group.truncate_table()
        Group.insert_many(groups).execute()

        return response(message='同步完成')

    @app.route('/group/getMemberList', methods=['POST'])
    def get_member_list():
        # members = bot.http.get_member_list(request.json['group_id'])
        # return response(members)
        return response(code=0, message='接口未开放')

    @app.route('/group/changeGroupStatus', methods=['POST'])
    def change_group_status():
        params = request.json
        group_id = params['group_id']

        if 'active' in params:
            GroupActive.insert(group_id=group_id, active=params['active']).on_conflict(
                conflict_target=[GroupActive.group_id],
                update={
                    GroupActive.active: params['active']
                }
            ).execute()
        else:
            for name in ['send_notice', 'send_weibo']:
                if name in params:
                    GroupSetting.insert(**{name: params[name], 'group_id': group_id}).on_conflict(
                        conflict_target=[GroupSetting.group_id],
                        update={
                            getattr(GroupSetting, name): params[name]
                        }
                    ).execute()

        return response(message='设置成功')

    @app.route('/group/leaveGroup', methods=['POST'])
    def leave_group():
        members = bot.http.leave_group(request.json['group_id'])
        return response(members)

    @app.route('/group/getGroupNoticeByPages', methods=['POST'])
    def get_group_notice_by_pages():
        params = request.json
        search = SearchParams(
            params['search'],
            contains=['content', 'send_user']
        )

        data, count = select_for_paginate(GroupNotice,
                                          search,
                                          page=params['page'],
                                          page_size=params['pageSize'])

        return response({'count': count, 'data': data})

    @app.route('/group/pushNotice', methods=['POST'])
    def push_notice():
        params = request.json
        user = session.get('user')

        threading.Timer(0, bot.push_notice, args=(user, params['content'])).start()

        GroupNotice.create(
            content=params['content'],
            send_time=int(time.time()),
            send_user=user
        )

        return response(message='开始推送公告')

    @app.route('/group/delNotice', methods=['POST'])
    @super_user
    def del_notice():
        params = request.json
        GroupNotice.delete().where(GroupNotice.notice_id == params['notice_id']).execute()
        return response(message='删除成功')
