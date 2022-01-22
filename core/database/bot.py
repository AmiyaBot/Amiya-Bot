from core.database import *

db = sqlite(db_conf.bot)


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
