from core.database import *
from typing import Union

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


@table
class GachaConfig(BotBaseModel):
    operator_name: str = CharField()
    operator_type: int = IntegerField()


@table
class Pool(BotBaseModel):
    pool_name: str = CharField(unique=True)
    pickup_6: str = CharField(null=True)
    pickup_5: str = CharField(null=True)
    pickup_4: str = CharField(null=True)
    pickup_s: str = CharField(null=True)
    limit_pool: int = IntegerField()


@table
class PoolSpOperator(BotBaseModel):
    pool_id: Union[ForeignKeyField, int] = ForeignKeyField(Pool, db_column='pool_id', on_delete='CASCADE')
    operator_name: str = CharField()
    rarity: int = IntegerField()
    classes: str = CharField()
    image: str = CharField()


@table
class TextReplace(BotBaseModel):
    user_id: str = CharField()
    group_id: str = CharField()
    origin: str = TextField()
    replace: str = TextField()
    in_time: int = BigIntegerField()
    is_global: int = IntegerField(default=0)
    is_active: int = IntegerField(default=1)


@table
class TextReplaceSetting(BotBaseModel):
    text: str = CharField()
    status: int = IntegerField()
