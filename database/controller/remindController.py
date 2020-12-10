import time


class Remind:
    def __init__(self, db):
        self.db = db

    def add_intellect_full_alarm(self, user_id, cur_num, full_num, full_time, message_type, group_id=0):
        cursor = self.db.cursor()

        now = int(time.time())
        update = ', '.join([
            'cur_num = %d' % cur_num,
            'full_num = %d' % full_num,
            'full_time = %d' % full_time,
            'message_type = "%s"' % message_type,
            'group_id = "%s"' % group_id,
            'in_time = %d' % now,
            'status = 0'
        ])
        sql_content = (user_id, cur_num, full_num, full_time, message_type, group_id, now, update)
        sql = 'INSERT INTO t_remind ( user_id, cur_num, full_num, full_time, message_type, group_id, in_time ) ' \
              'VALUES ( "%s", %d, %d, %d, "%s", "%s", %d ) ' \
              'ON DUPLICATE KEY UPDATE %s' % sql_content

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def check_intellect_full_alarm(self, full_time):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_remind WHERE status = 0 AND full_time <= %d' % full_time

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        self.update_intellect_full_alarm(full_time)

        return res

    def update_intellect_full_alarm(self, full_time):
        cursor = self.db.cursor()

        sql = 'UPDATE t_remind SET status = 1 WHERE full_time <= %d' % full_time

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def check_intellect_by_user(self, user_id):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_remind WHERE user_id = "%s"' % user_id

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchone()

        return res
