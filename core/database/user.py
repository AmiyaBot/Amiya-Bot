from core.database import *
from typing import Union

db = connect_database(databases.user)


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
class Admin(UserBaseModel):
    user_id = CharField(primary_key=True)
    password = CharField()
    last_login = BigIntegerField(null=True)
    last_login_ip = CharField(null=True)
    active = IntegerField(default=1)
