from amiyabot import AmiyaBot, KOOKBotInstance
from amiyabot.database import *
from amiyabot.adapters.mirai import mirai_api_http
from amiyabot.adapters.cqhttp import cq_http
from core.database import config, is_mysql
from typing import Union

db = connect_database('amiya_bot' if is_mysql else 'database/amiya_bot.db', is_mysql, config)


class BotBaseModel(ModelClass):
    class Meta:
        database = db


@table
class Admin(BotBaseModel):
    account: Union[CharField, str] = CharField(unique=True)
    remark: Union[CharField, str] = CharField(null=True)


@table
class BotAccounts(BotBaseModel):
    appid: str = CharField(unique=True)
    token: str = CharField()
    private: int = SmallIntegerField(default=0)
    is_start: int = SmallIntegerField(default=1)
    is_main: int = SmallIntegerField(default=0)
    console_channel: str = CharField(null=True)
    adapter: str = CharField(default='tencent')

    mah_host: str = CharField(null=True)
    mah_ws_port: int = IntegerField(null=True)
    mah_http_port: int = IntegerField(null=True)

    cq_host: str = CharField(null=True)
    cq_ws_port: int = IntegerField(null=True)
    cq_http_port: int = IntegerField(null=True)

    @classmethod
    def get_all_account(cls):
        select: List[cls] = cls.select()
        account = []

        for item in select:
            if not item.is_start:
                continue

            conf = {
                'appid': item.appid,
                'token': item.token,
                'private': bool(item.private)
            }
            if item.adapter == 'mirai_api_http':
                conf['adapter'] = mirai_api_http(host=item.mah_host,
                                                 ws_port=item.mah_ws_port,
                                                 http_port=item.mah_http_port)
            if item.adapter == 'cq_http':
                conf['adapter'] = cq_http(host=item.cq_host,
                                          ws_port=item.cq_ws_port,
                                          http_port=item.cq_http_port)
            if item.adapter == 'kook':
                conf['adapter'] = KOOKBotInstance

            account.append(AmiyaBot(**conf))

        return account


@table
class FunctionUsed(BotBaseModel):
    function_id: str = CharField(primary_key=True)
    use_num: int = IntegerField(default=1)


@table
class DisabledFunction(BotBaseModel):
    function_id: str = CharField(null=True)
    channel_id: str = CharField(null=True)


@table
class OperatorIndex(BotBaseModel):
    name: Union[CharField, str] = CharField()
    en_name: Union[CharField, str] = CharField()
    rarity: Union[CharField, str] = CharField()
    classes: Union[CharField, str] = CharField()
    classes_sub: Union[CharField, str] = CharField()
    classes_code: Union[CharField, str] = CharField()
    type: Union[CharField, str] = CharField()


@table
class OperatorConfig(BotBaseModel):
    operator_name: str = CharField()
    operator_type: int = IntegerField()


@table
class Pool(BotBaseModel):
    pool_name: Union[CharField, str] = CharField(unique=True)
    pickup_6: Union[CharField, str] = CharField(null=True, default='')
    pickup_5: Union[CharField, str] = CharField(null=True, default='')
    pickup_4: Union[CharField, str] = CharField(null=True, default='')
    pickup_s: Union[CharField, str] = CharField(null=True, default='')
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
    origin: Union[TextField, str] = TextField()
    replace: Union[TextField, str] = TextField()
    in_time: int = BigIntegerField()
    is_user_only: int = IntegerField(default=0)
    is_global: int = IntegerField(default=0)
    is_active: int = IntegerField(default=1)


@table
class TextReplaceSetting(BotBaseModel):
    text: str = CharField(unique=True)
    status: int = IntegerField()
