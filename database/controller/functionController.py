class Function:
    def __init__(self, db):
        self.db = db

    def add_function_use_num(self, function_id):
        cursor = self.db.cursor()

        sql = 'INSERT INTO t_function ( function_id, function_use_num ) VALUES ( "%s", 1 ) ' \
              'ON DUPLICATE KEY UPDATE function_use_num = function_use_num + 1' % function_id

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def get_all_function_use_num(self):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_function'

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res
