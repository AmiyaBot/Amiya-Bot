from typing import Union
from core.database import *
from core.config import config

db = connect_database(databases.group)


class GroupBaseModel(ModelClass):
    class Meta:
        database = db


@table
class Group(GroupBaseModel):
    group_id: Union[CharField, str] = CharField(primary_key=True)
    group_name: str = CharField()
    permission: str = CharField()


@table
class GroupActive(GroupBaseModel):
    group_id: str = CharField(primary_key=True)
    active: int = IntegerField(default=1)
    sleep_time: int = BigIntegerField(default=0)


@table
class GroupSetting(GroupBaseModel):
    group_id: str = CharField(primary_key=True)
    send_notice: int = IntegerField(default=1, null=True)
    send_weibo: int = IntegerField(default=0, null=True)


@table
class GroupNotice(GroupBaseModel):
    content = CharField()
    send_time = BigIntegerField()
    send_user = CharField()


def check_group_active(group_id):
    if config.test.enable:
        if int(group_id) not in config.test.group:
            return False

    group: GroupActive = GroupActive.get_or_none(group_id=group_id)
    if group and group.active == 0:
        return False
    return True
