from core.database import *
from core.database.user import User as UserData, UserInfo, UserGachaInfo

amiya = SqliteDatabase('amiya.db')


class AmiyaBaseModel(Model):
    class Meta:
        database = amiya


class User(AmiyaBaseModel):
    user_id = TextField(primary_key=True)
    user_feeling = IntegerField(default=0)
    user_mood = IntegerField(default=15)
    message_num = IntegerField(default=0)
    coupon = IntegerField(default=50)
    gacha_break_even = IntegerField(default=0)
    gacha_pool = IntegerField(default=1)
    sign_in = IntegerField(default=0)
    sign_times = IntegerField(default=0)
    black = IntegerField(default=0)
    waiting = TextField(null=True)


def transfer_user():
    all_user: List[User] = User.select()

    user_data = []
    user_info_data = []
    user_gacha_info_data = []

    for item in all_user:
        user_data.append({
            'user_id': item.user_id,
            'nickname': '',
            'message_num': item.message_num,
            'black': item.black,
        })
        user_info_data.append({
            'user_id': item.user_id,
            'user_feeling': item.user_feeling,
            'user_mood': item.user_mood,
            'sign_in': item.sign_in,
            'sign_times': item.sign_times,
        })
        user_gacha_info_data.append({
            'user_id': item.user_id,
            'coupon': item.coupon,
            'gacha_break_even': item.gacha_break_even,
            'gacha_pool': item.gacha_pool,
        })

    UserData.delete().execute()
    UserInfo.delete().execute()
    UserGachaInfo.delete().execute()

    UserData.batch_insert(user_data, chunk_size=100)
    UserInfo.batch_insert(user_info_data, chunk_size=100)
    UserGachaInfo.batch_insert(user_gacha_info_data, chunk_size=100)


if __name__ == '__main__':
    transfer_user()
