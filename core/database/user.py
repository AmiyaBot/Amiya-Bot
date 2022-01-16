from core.database import *
from core.config import config

db = sqlite(config.databases.user)


class BaseModel(Model):
    class Meta:
        database = db


@table
class User(BaseModel):
    user_id = TextField(primary_key=True)
    nickname = TextField(null=True)
    message_num = IntegerField(default=0)
    black = IntegerField(default=0)
