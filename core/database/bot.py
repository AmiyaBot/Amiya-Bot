from amiyabot import AmiyaBot, KOOKBotInstance
from amiyabot.database import *
from amiyabot.adapters.mirai import mirai_api_http
from amiyabot.adapters.cqhttp import cq_http
from amiyabot.adapters.onebot11 import onebot11
from amiyabot.adapters.onebot12 import onebot12
from amiyabot.adapters.comwechat import com_wechat
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

    @classmethod
    def is_super_admin(cls, user_id: str):
        return bool(cls.get_or_none(account=user_id))


@table
class BotAccounts(BotBaseModel):
    appid: str = CharField(unique=True)
    token: str = CharField()
    private: int = SmallIntegerField(default=0)
    is_start: int = SmallIntegerField(default=1)
    is_main: int = SmallIntegerField(default=0)
    console_channel: str = CharField(null=True)
    adapter: str = CharField(default='tencent')

    host: str = CharField(null=True)
    ws_port: int = IntegerField(null=True)
    http_port: int = IntegerField(null=True)

    @classmethod
    def get_all_account(cls):
        select: List[cls] = cls.select()
        account = []

        net_adapters = {
            'mirai_api_http': mirai_api_http,
            'cq_http': cq_http,
            'onebot11': onebot11,
            'onebot12': onebot12,
            'com_wechat': com_wechat,
        }

        for item in select:
            if not item.is_start:
                continue

            conf = {
                'appid': item.appid,
                'token': item.token,
                'private': bool(item.private),
            }

            if item.adapter in net_adapters:
                conf['adapter'] = net_adapters[item.adapter](
                    host=item.host,
                    ws_port=item.ws_port,
                    http_port=item.http_port,
                )

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
