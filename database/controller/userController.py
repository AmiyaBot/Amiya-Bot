from database.sqlCombiner import Mysql, Formula, Where


class User:
    def __init__(self, db: Mysql):
        self.db = db

    def update_user(self, user_id, feeling, coupon=0, message_num=0, sign=0):
        data = {
            'user_id': user_id,
            'user_feeling': feeling,
            'coupon': coupon,
            'message_num': message_num,
            'sign_in': sign,
            'sign_times': sign,
        }
        update = {
            'user_feeling': Formula('user_feeling + %d' % feeling),
            'user_mood': Formula('IF (user_mood + {feeling} <= 15 AND user_mood + {feeling} >= -10, '
                                 'user_mood + {feeling}, '
                                 'user_mood)'.format(feeling=feeling)),
            'coupon': Formula('coupon + %d' % coupon),
            'message_num': Formula('message_num + %d' % message_num)
        }
        if sign:
            update['sign_in'] = sign
            update['sign_times'] = Formula('sign_times + %d' % sign)

        self.db.insert(
            table='t_user',
            data=data,
            update=update
        )

    def get_user(self, user_id):
        return self.db.select('t_user', where=Where({'user_id': user_id}), fetchone=True)

    def get_black_user(self, user_id):
        return self.db.select('t_user', where=Where({'user_id': user_id, 'black': 1}), fetchone=True)

    def set_black_user(self, user_id):
        self.db.update(
            table='t_user',
            where=Where({'user_id': user_id}),
            data={
                'black': 1
            }
        )

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

    def set_break_even(self, user_id, break_even, costs):
        self.db.update(
            table='t_user',
            where=Where({'user_id': user_id}),
            data={
                'gacha_break_even': break_even,
                'coupon': Formula('coupon - %d' % costs)
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
