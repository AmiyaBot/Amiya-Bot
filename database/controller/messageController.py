import time

from database.sqlCombiner import Mysql, Formula, Where


class Message:
    def __init__(self, db: Mysql):
        self.db = db

    def add_message(self, target_id, msg_type, reply_user=0):
        now = time.time()
        hour = int(time.strftime('%H', time.localtime(now)))

        self.db.insert('t_message', data={
            'target_id': target_id,
            'msg_type': msg_type,
            'reply_user': reply_user,
            'msg_time': int(now),
            'hour_mark': hour
        })

    def del_message(self):
        self.db.truncate('t_message')

    def check_message_speed_by_user(self, user_id, seconds):
        return self.db.count('t_message', 'msg_id', where=Where({
            'reply_user': user_id,
            'msg_time': ['>=', time.time() - seconds]
        }))
