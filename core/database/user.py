from core.database import *
from typing import Union

db = sqlite(db_conf.user)


class UserBaseModel(Model):
    class Meta:
        database = db


@table
class User(UserBaseModel):
    user_id: Union[TextField, str] = TextField(primary_key=True)
    nickname: str = TextField(null=True)
    message_num: int = IntegerField(default=0)
    black: int = IntegerField(default=0)


@table
class Admin(UserBaseModel):
    user_id = TextField(primary_key=True)
    password = TextField()
    last_login = BigIntegerField(null=True)
    last_login_ip = TextField(null=True)
    active = IntegerField(default=1)
