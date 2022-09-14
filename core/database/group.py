from amiyabot.database import *
from core.database import config, is_mysql
from typing import Union

db = connect_database('amiya_group' if is_mysql else 'database/amiya_group.db', is_mysql, config)


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
    bot_id: str = CharField(null=True)
    send_notice: int = IntegerField(default=1, null=True)
    send_weibo: int = IntegerField(default=0, null=True)


def check_group_active(group_id):
    group: GroupActive = GroupActive.get_or_none(group_id=group_id)
    return not (group and group.active == 0)
