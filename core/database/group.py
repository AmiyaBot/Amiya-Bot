from core.database import *
from typing import Union

db = sqlite(db_conf.group)


class GroupBaseModel(Model):
    class Meta:
        database = db


@table
class Group(GroupBaseModel):
    group_id: Union[TextField, str] = TextField(primary_key=True)
    group_name: str = TextField()
    permission: str = TextField()


@table
class GroupActive(GroupBaseModel):
    group_id: str = TextField(primary_key=True)
    active: int = IntegerField(default=1)
    sleep_time: int = BigIntegerField(default=0)


@table
class GroupSetting(GroupBaseModel):
    group_id: str = TextField(primary_key=True)
    send_notice: int = IntegerField(default=1, null=True)
    send_weibo: int = IntegerField(default=0, null=True)


@table
class GroupNotice(GroupBaseModel):
    content = TextField()
    send_time = BigIntegerField()
    send_user = TextField()
