from core.database import *
from typing import Union

db = connect_database(databases.user)
game = read_yaml('config/private/game.yaml')


class UserBaseModel(ModelClass):
    class Meta:
        database = db


@table
class User(UserBaseModel):
    user_id: Union[CharField, str] = CharField(primary_key=True)
    nickname: str = CharField(null=True)
    message_num: int = IntegerField(default=0)
    black: int = IntegerField(default=0)


@table
class Role(UserBaseModel):
    role_name: str = CharField(null=True)
    access_path: str = TextField(null=True)
    active: int = IntegerField(default=1)


@table
class Admin(UserBaseModel):
    user_id = CharField(primary_key=True)
    role_id: Role = ForeignKeyField(Role, db_column='role_id', on_delete='SET NULL', null=True)
    password = CharField()
    last_login = BigIntegerField(null=True)
    last_login_ip = CharField(null=True)
    active = IntegerField(default=1)


@table
class OperatorBox(UserBaseModel):
    user_id: str = CharField()
    operator: str = TextField(default='')


@table
class Intellect(UserBaseModel):
    user_id: str = CharField(primary_key=True)
    cur_num: int = IntegerField()
    full_num: int = IntegerField()
    full_time: int = IntegerField()
    message_type: str = CharField()
    group_id: str = CharField()
    in_time: int = IntegerField()
    status: int = IntegerField()


@table
class UserInfo(UserBaseModel):
    user_id: Union[ForeignKeyField, str] = ForeignKeyField(User, db_column='user_id', on_delete='CASCADE')
    user_feeling: int = IntegerField(default=0)
    user_mood: int = IntegerField(default=15)
    sign_in: int = IntegerField(default=0)
    sign_times: int = IntegerField(default=0)
    jade_point: int = IntegerField(default=0)
    jade_point_max: int = IntegerField(default=0)
    times_report: int = IntegerField(default=0)

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
