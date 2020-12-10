class User:
    def __init__(self, db):
        self.db = db

    def get_black_user(self):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_user WHERE black = 1'

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def set_black_user(self, user_id):
        cursor = self.db.cursor()

        sql = 'UPDATE t_user SET black = 1 WHERE user_id = "%s"' % user_id

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def add_feeling(self, user_id, feeling, sign):
        cursor = self.db.cursor()

        update = [
            'user_feeling = user_feeling + %d' % feeling,
            'user_mood = IF (user_mood + %d <= 15 AND user_mood + %d >= - 10, '
            'user_mood + %d, user_mood)' % (feeling, feeling, feeling)
        ]
        if sign:
            update.append('sign_in = %d' % sign)
        sql = 'INSERT INTO t_user ( user_id, user_feeling, sign_in ) VALUES ( "%s", %d, %d ) ' \
              'ON DUPLICATE KEY UPDATE %s' % (user_id, feeling, sign, ', '.join(update))

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def add_coupon(self, user_id, num):
        cursor = self.db.cursor()

        sql = 'UPDATE t_user SET gacha_coupon = gacha_coupon + %d WHERE user_id = "%s"' % (num, user_id)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def set_break_even(self, user_id, break_even, costs):
        cursor = self.db.cursor()

        sql = 'UPDATE t_user SET gacha_break_even = %d, ' \
              'gacha_coupon = gacha_coupon - %d WHERE user_id = "%s"' % (break_even, costs, user_id)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def get_user(self, user_id):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_user WHERE user_id = "%s"' % user_id

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchone()

        return res

    def get_gacha_pool(self, user_id=None):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_pool'

        if user_id is not None:
            sql += ' WHERE pool_id IN (SELECT gacha_pool FROM t_user WHERE user_id = "%s")' % user_id

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def set_gacha_pool(self, user_id, pool_id):
        cursor = self.db.cursor()

        sql = 'UPDATE t_user SET gacha_pool = %d WHERE user_id = "%s"' % (pool_id, user_id)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def reset_mood(self):
        cursor = self.db.cursor()

        sql = 'UPDATE t_user SET user_mood = 15 WHERE user_mood < 15'

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def reset_sign(self):
        cursor = self.db.cursor()

        sql = 'UPDATE t_user SET sign_in = 0'

        self.db.ping(reconnect=True)
        cursor.execute(sql)
