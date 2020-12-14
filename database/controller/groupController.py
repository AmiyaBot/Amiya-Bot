import time


class Group:
    def __init__(self, db):
        self.db = db

    def record_group(self, group_id):
        cursor = self.db.cursor()

        sql = 'INSERT INTO t_group ( group_id, in_time ) VALUES ( "%s", %d )' % (group_id, int(time.time()))

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def add_group_msg_num(self, group_id, msg_num=0, use_num=0):
        cursor = self.db.cursor()

        sql = 'UPDATE t_group SET msg_total = msg_total + %d, use_total = use_total + %d ' \
              'WHERE group_id = "%s"' % (msg_num, use_num, group_id)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def delete_group(self, group_id):
        cursor = self.db.cursor()

        sql = 'DELETE FROM t_group WHERE group_id = "%s"' % group_id

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def delete_group_msg(self, group_id):
        cursor = self.db.cursor()

        sql = 'DELETE FROM t_message WHERE target_id = "%s"' % group_id

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def get_all_group(self):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_group'

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def add_ignore_group(self, group_id):
        cursor = self.db.cursor()

        sql = 'INSERT INTO t_ignore_group ( group_id ) VALUES ( "%s" )' % group_id

        try:
            self.db.ping(reconnect=True)
            cursor.execute(sql)
        except Exception as e:
            print('Mysql', e)

    def get_all_ignore_group(self):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_ignore_group'

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res
