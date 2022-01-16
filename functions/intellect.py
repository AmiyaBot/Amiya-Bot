from core import bot, Message, Chain
from core.database.user import *


@table
class Intellect(BaseModel):
    user_id = TextField(primary_key=True)
    cur_num = IntegerField()
    full_num = IntegerField()
    full_time = IntegerField()
    message_type = TextField()
    group_id = TextField()
    in_time = IntegerField()
    status = IntegerField()
