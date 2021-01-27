from database.sqlCombiner import Mysql, Calc, Where


class User:
    def __init__(self, db: Mysql):
        self.db = db

    def add_feeling(self, user_id, feeling, sign):
        data = {
            'user_id': user_id,
            'user_feeling': feeling,
            'sign_in': sign
        }
        update = {
            'user_feeling': Calc('user_feeling + %d' % feeling),
            'user_mood': Calc('IF (user_mood + %d <= 15 AND user_mood + %d >= - 10, user_mood + %d, user_mood)'
                              % (feeling, feeling, feeling))
        }
        if sign:
            update['sign_in'] = sign

        self.db.insert(
            table='t_user',
            data=data,
            update=update
        )

    def add_coupon(self, user_id, num):
        self.db.update(
            table='t_user',
            where=Where({'user_id': user_id}),
            data={
                'gacha_coupon': Calc('gacha_coupon + %d' % num)
            }
        )

    def set_break_even(self, user_id, break_even, costs):
        self.db.update(
            table='t_user',
            where=Where({'user_id': user_id}),
            data={
                'gacha_break_even': break_even,
                'gacha_coupon': Calc('gacha_coupon - %d' % costs)
            }
        )

    def get_user(self, user_id):
        return self.db.select('t_user', where=Where({'user_id': user_id}), fetchone=True)

    def get_gacha_pool(self, user_id=None):
        where = ('pool_id IN (SELECT gacha_pool FROM t_user WHERE user_id = %s)' % user_id) if user_id else None
        return self.db.select('t_pool', where=where, fetchone=bool(user_id))

    def set_gacha_pool(self, user_id, pool_id):
        self.db.update(
            table='t_user',
            where=Where({'user_id': user_id}),
            data={
                'gacha_pool': pool_id
            }
        )

    def set_waiting(self, user_id, name):
        self.db.update(
            table='t_user',
            where=Where({'user_id': user_id}),
            data={
                'waiting': name
            }
        )

    def reset_state(self):
        self.db.update(
            table='t_user',
            data={
                'user_mood': 15,
                'sign_in': 0
            }
        )
