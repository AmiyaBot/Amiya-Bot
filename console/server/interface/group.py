import time
import threading

from flask import Flask, session, request

from core import AmiyaBot
from core.database.models import sqlite_db, Group, GroupActive, GroupSetting, GroupNotice
from core.database.manager import select_for_paginate

from ..response import response
from .auth import super_user


def group_controller(app: Flask, bot: AmiyaBot):
    @app.route('/group/getGroupByPages', methods=['POST'])
    def get_group_by_pages():
        params = request.json
        where = []
        if params['search']:
            if params['search']['group_id']:
                where.append(f"g.group_id like '%{params['search']['group_id']}%'")
            if params['search']['group_name']:
                where.append(f"g.group_name like '%{params['search']['group_name']}%'")
            if params['search']['permission']:
                where.append(f"g.permission = '{params['search']['permission']}'")
            if params['search']['active']:
                where.append(f"g2.active = '{params['search']['active']}'")
            if params['search']['send_notice']:
                where.append(f"g3.send_notice = '{params['search']['send_notice']}'")
            if params['search']['send_weibo']:
                where.append(f"g3.send_weibo = '{params['search']['send_weibo']}'")
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
                 left join groupsleep g2 on g.group_id = g2.group_id
                 left join groupsetting g3 on g.group_id = g3.group_id
                 left join (select count(*) message_num, group_id from message where record = 'call' group by group_id)
                           g4 on g.group_id = g4.group_id {where if where else ''}
        order by g4.message_num desc
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
        contains = {}

        if params['search']:
            contains = {
                'content': params['search']['content'],
                'send_user': params['search']['send_user']
            }

        data, count = select_for_paginate(GroupNotice,
                                          contains=contains,
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
