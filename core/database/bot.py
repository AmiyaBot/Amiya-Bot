from core.database import *
from core.config import config

db = sqlite(config.databases.bot)


class BaseModel(Model):
    class Meta:
        database = db


@table
class FunctionUsed(BaseModel):
    function_id = TextField(primary_key=True)
    use_num = IntegerField(default=1)


@table
class DisabledFunction(BaseModel):
    function_id = TextField()
    group_id = TextField()
    status = IntegerField()
