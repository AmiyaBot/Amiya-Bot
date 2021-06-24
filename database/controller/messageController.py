import time

from database.sqlCombiner import Mysql, Formula, Where


class Message:
    def __init__(self, db: Mysql):
        self.db = db

    def add_message(self, msg_type, user_id, group_id=0, reply_user=0):
        self.db.insert('t_message', data={
            'msg_type': msg_type,
            'group_id': group_id,
            'user_id': user_id,
            'reply_user': reply_user,
            'msg_time': int(time.time())
        })

    def del_message(self, days: int):
        last_time = int(time.time()) - days * 86400

        self.db.delete('t_message', where=Where({
            'msg_time': ['<=', last_time]
        }))

    def check_message_speed_by_user(self, user_id, seconds):
        return self.db.count('t_message', 'msg_id', where=Where({
            'reply_user': user_id,
            'msg_time': ['>=', time.time() - seconds]
        }))
