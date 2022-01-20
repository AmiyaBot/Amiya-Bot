from core.database import *
from core.config import config

db = sqlite(config.databases.group)


class GroupBaseModel(Model):
    class Meta:
        database = db


@table
class Group(GroupBaseModel):
    group_id: str = TextField(primary_key=True)
    group_name: str = TextField()
    permission: str = TextField()


@table
class GroupActive(GroupBaseModel):
    group_id: str = TextField(primary_key=True)
    active: int = IntegerField(default=1)
    sleep_time: int = BigIntegerField(default=0)
