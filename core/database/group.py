from core.database import *
from core.config import config

db = sqlite(config.databases.group)


class BaseModel(Model):
    class Meta:
        database = db


@table
class Group(BaseModel):
    group_id = TextField(primary_key=True)
    group_name = TextField()
    permission = TextField()


@table
class GroupActive(BaseModel):
    group_id = TextField(primary_key=True)
    active = IntegerField(default=1)
    sleep_time = BigIntegerField(default=0)
