import time


class Message:
    def __init__(self, db):
        self.db = db

    def add_message(self, target_id, msg_type, reply_user=0):
        cursor = self.db.cursor()

        now = time.time()
        hour = int(time.strftime('%H', time.localtime(now)))

        sql = 'INSERT INTO t_message ( target_id, msg_type, reply_user, msg_time, hour_mark ) VALUES ' \
              '( "%s", "%s", "%s", %d, %d )' % (target_id, msg_type, reply_user, now, hour)

        try:
            self.db.ping(reconnect=True)
            cursor.execute(sql)
        except Exception as e:
            print('Mysql', e)

    def delete_old_message(self):
        cursor = self.db.cursor()

        sql = 'DELETE FROM t_message WHERE msg_time < %d' % get_last_time()

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def check_message_num(self):
        cursor = self.db.cursor()

        sql = 'SELECT count( hour_mark ), hour_mark, msg_time FROM t_message ' \
              'WHERE msg_time >= %d GROUP BY hour_mark' % get_last_time()

        self.delete_old_message()
        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def check_message_type(self):
        cursor = self.db.cursor()

        sql = 'SELECT count( msg_type ), msg_type FROM t_message WHERE msg_time >= %d GROUP BY msg_type' % get_last_time()

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def check_message_speed(self):
        cursor = self.db.cursor()

        last = time.time() - 60
        sql = 'SELECT count( msg_id ) FROM t_message WHERE msg_time >= %d' % last

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchone()

        return res

    def check_message_speed_by_user(self, user_id, seconds):
        cursor = self.db.cursor()

        last = time.time() - seconds
        sql = 'SELECT count( msg_id ) FROM t_message WHERE reply_user = "%s" AND msg_time >= %d' % (user_id, last)

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchone()

        return res


def get_last_time():
    last = time.time() - 43200
    last = time.strftime('%Y-%m-%d %H:00:00', time.localtime(last))
    last = int(time.mktime(time.strptime(last, '%Y-%m-%d %H:%M:%S')))

    return last
