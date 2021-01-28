import time

from database.sqlCombiner import Mysql, Formula, Where


class Remind:
    def __init__(self, db: Mysql):
        self.db = db

    def add_intellect_full_alarm(self, user_id, cur_num, full_num, full_time, message_type, group_id=0):
        now = int(time.time())
        data = {
            'user_id': user_id,
            'cur_num': cur_num,
            'full_num': full_num,
            'full_time': full_time,
            'message_type': message_type,
            'group_id': group_id,
            'in_time': now,
        }
        update = {
            'cur_num': cur_num,
            'full_num': full_num,
            'full_time': full_time,
            'message_type': message_type,
            'group_id': group_id,
            'in_time': now,
            'status': 0
        }
        self.db.insert('t_remind', data=data, update=update)

    def check_intellect_full_alarm(self, full_time):
        res = self.db.select('t_remind', where=Where({
            'status': 0,
            'full_time': ['<=', full_time]
        }))

        self.update_intellect_full_alarm(full_time)

        return res

    def update_intellect_full_alarm(self, full_time):
        self.db.update('t_remind', where=Where({
            'full_time': ['<=', full_time]
        }), data={
            'status': 1
        })

    def check_intellect_by_user(self, user_id):
        return self.db.select('t_remind', where=Where({
            'user_id': user_id
        }), fetchone=True)
