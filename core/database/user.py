from core.database import *

db = sqlite(db_conf.user)


class UserBaseModel(Model):
    class Meta:
        database = db


@table
class User(UserBaseModel):
    user_id: str = TextField(primary_key=True)
    nickname: str = TextField(null=True)
    message_num: int = IntegerField(default=0)
    black: int = IntegerField(default=0)
