from core.database.user import *
from core.util import read_yaml

game = read_yaml('config/private/game.yaml')


@table
class UserInfo(UserBaseModel):
    user_id: Union[ForeignKeyField, str] = ForeignKeyField(User, db_column='user_id', on_delete='CASCADE')
    user_feeling: int = IntegerField(default=0)
    user_mood: int = IntegerField(default=15)
    sign_in: int = IntegerField(default=0)
    sign_times: int = IntegerField(default=0)
    jade_point: int = IntegerField(default=0)
    jade_point_max: int = IntegerField(default=0)

    @classmethod
    def get_user(cls, user_id):
        return cls.get_or_create(user_id=user_id)[0]

    @classmethod
    def add_jade_point(cls, user_id, point):
        user: UserInfo = cls.get_user(user_id)

        surplus = game.jade_point_max - user.jade_point_max
        if surplus <= 0:
            return None

        if point > surplus:
            point = surplus

        update = {
            'jade_point': UserInfo.jade_point + point,
            'jade_point_max': UserInfo.jade_point_max + point
        }
        cls.update(**update).where(UserInfo.user_id == user_id).execute()


@table
class UserGachaInfo(UserBaseModel):
    user_id: Union[ForeignKeyField, str] = ForeignKeyField(User, db_column='user_id', on_delete='CASCADE')
    coupon: int = IntegerField(default=50)
    gacha_break_even: int = IntegerField(default=0)
    gacha_pool: int = IntegerField(default=1)
