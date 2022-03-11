from core.database import *

db = connect_database(databases.bot)


class BotBaseModel(ModelClass):
    class Meta:
        database = db


@table
class FunctionUsed(BotBaseModel):
    function_id: str = CharField(primary_key=True)
    use_num: int = IntegerField(default=1)


@table
class DisabledFunction(BotBaseModel):
    function_id: str = CharField()
    group_id: str = CharField()
    status: int = IntegerField()
