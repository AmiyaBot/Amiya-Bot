from amiyabot.database import *
from core.database import config, is_mysql

db = connect_database('amiya_message' if is_mysql else 'database/amiya_message.db', is_mysql, config)


class MessageBaseModel(ModelClass):
    class Meta:
        database = db


@table
class MessageRecord(MessageBaseModel):
    app_id: str = CharField(null=True)
    user_id: str = CharField()
    channel_id: str = CharField(null=True)
    msg_type: str = CharField()
    classify: str = CharField(null=True)
    create_time: int = IntegerField()
