from core.database import *
from core.config import config

db = sqlite(config.databases.bot)


class BotBaseModel(Model):
    class Meta:
        database = db


@table
class FunctionUsed(BotBaseModel):
    function_id: str = TextField(primary_key=True)
    use_num: int = IntegerField(default=1)


@table
class DisabledFunction(BotBaseModel):
    function_id: str = TextField()
    group_id: str = TextField()
    status: int = IntegerField()
