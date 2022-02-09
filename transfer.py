from core.database import *
from core.database.user import User as UserData, Admin as AdminData
from core.database.bot import FunctionUsed, DisabledFunction
from core.resource.arknightsGameData.common import GachaConfig as GachaConfigData
from functions.user import UserInfo
from functions.intellect import Intellect as IntellectData
from functions.replace import TextReplace
from functions.arknights.gacha import UserGachaInfo
from functions.arknights.gacha.gacha import Pool as PoolData

amiya = sqlite('database/amiya.db')


class AmiyaBaseModel(Model):
    class Meta:
        database = amiya


class User(AmiyaBaseModel):
    user_id = TextField(primary_key=True)
    user_feeling = IntegerField(default=0)
    user_mood = IntegerField(default=15)
    message_num = IntegerField(default=0)
    coupon = IntegerField(default=50)
    gacha_break_even = IntegerField(default=0)
    gacha_pool = IntegerField(default=1)
    sign_in = IntegerField(default=0)
    sign_times = IntegerField(default=0)
    black = IntegerField(default=0)
    waiting = TextField(null=True)


class Admin(AmiyaBaseModel):
    user_id = TextField(primary_key=True)
    password = TextField()
    last_login = BigIntegerField(null=True)
    last_login_ip = TextField(null=True)
    active = IntegerField(default=1)


class Intellect(AmiyaBaseModel):
    user_id = TextField(primary_key=True)
    cur_num = IntegerField()
    full_num = IntegerField()
    full_time = BigIntegerField()
    message_type = TextField()
    group_id = TextField()
    in_time = BigIntegerField()
    status = IntegerField()


class ReplaceText(AmiyaBaseModel):
    replace_id = IntegerField(primary_key=True, constraints=[SQL('autoincrement')])
    user_id = TextField()
    group_id = TextField()
    origin = TextField()
    target = TextField()
    in_time = BigIntegerField()
    is_global = IntegerField(default=0)
    is_active = IntegerField(default=1)


class Function(AmiyaBaseModel):
    function_id = TextField(primary_key=True)
    use_num = IntegerField(default=1)


class Disable(AmiyaBaseModel):
    group_id = TextField()
    function_id = TextField()
    status = IntegerField()


class Pool(AmiyaBaseModel):
    pool_id = IntegerField(primary_key=True, constraints=[SQL('autoincrement')])
    pool_name = TextField(unique=True)
    pickup_6 = TextField(null=True)
    pickup_5 = TextField(null=True)
    pickup_4 = TextField(null=True)
    pickup_s = TextField(null=True)
    limit_pool = IntegerField()


class GachaConfig(AmiyaBaseModel):
    conf_id = IntegerField(primary_key=True, constraints=[SQL('autoincrement')])
    operator_name = TextField()
    operator_type = IntegerField()


def transfer_user():
    all_user: List[User] = User.select()

    user_data = []
    user_info_data = []
    user_gacha_info_data = []

    for item in all_user:
        user_data.append({
            'user_id': item.user_id,
            'nickname': '',
            'message_num': item.message_num,
            'black': item.black,
        })
        user_info_data.append({
            'user_id': item.user_id,
            'user_feeling': item.user_feeling,
            'user_mood': item.user_mood,
            'sign_in': item.sign_in,
            'sign_times': item.sign_times,
        })
        user_gacha_info_data.append({
            'user_id': item.user_id,
            'coupon': item.coupon,
            'gacha_break_even': item.gacha_break_even,
            'gacha_pool': item.gacha_pool,
        })

    UserGachaInfo.delete().execute()
    UserInfo.delete().execute()
    UserData.delete().execute()

    UserData.insert_data(user_data)
    UserInfo.insert_data(user_info_data)
    UserGachaInfo.insert_data(user_gacha_info_data)


def transfer_admin():
    all_admin: List[Admin] = Admin.select()

    data = []

    for item in all_admin:
        data.append({
            'user_id': item.user_id,
            'password': item.password,
            'last_login': item.last_login,
            'last_login_ip': item.last_login_ip,
            'active': item.active,
        })

    AdminData.delete().execute()
    AdminData.insert_data(data)


def transfer_replace():
    all_data: List[ReplaceText] = ReplaceText.select()

    data = []

    for item in all_data:
        data.append({
            'user_id': item.user_id,
            'group_id': item.group_id,
            'origin': item.origin,
            'replace': item.target,
            'in_time': item.in_time,
            'is_global': item.is_global,
            'is_active': item.is_active,
        })

    TextReplace.delete().execute()
    TextReplace.insert_data(data)


def transfer_intellect():
    all_data: List[Intellect] = Intellect.select()

    data = []

    for item in all_data:
        data.append({
            'user_id': item.user_id,
            'cur_num': item.cur_num,
            'full_num': item.full_num,
            'full_time': item.full_time,
            'message_type': item.message_type,
            'group_id': item.group_id,
            'in_time': item.in_time,
            'status': item.status,
        })

    IntellectData.delete().execute()
    IntellectData.insert_data(data)


def transfer_function():
    all_data: List[Function] = Function.select()

    data = []

    for item in all_data:
        data.append({
            'function_id': item.function_id,
            'use_num': item.use_num
        })

    FunctionUsed.delete().execute()
    FunctionUsed.insert_data(data)


def transfer_disable():
    all_data: List[Disable] = Disable.select()

    data = []

    for item in all_data:
        data.append({
            'function_id': item.function_id,
            'group_id': item.group_id,
            'status': item.status
        })

    DisabledFunction.delete().execute()
    DisabledFunction.insert_data(data)


def transfer_pool():
    all_data: List[Pool] = Pool.select()

    data = []

    for item in all_data:
        data.append({
            'pool_name': item.pool_name,
            'pickup_6': item.pickup_6,
            'pickup_5': item.pickup_5,
            'pickup_4': item.pickup_4,
            'pickup_s': item.pickup_s,
            'limit_pool': item.limit_pool,
        })

    PoolData.delete().execute()
    PoolData.insert_data(data)


def transfer_gacha_config():
    all_data: List[GachaConfig] = GachaConfig.select()

    data = []

    for item in all_data:
        data.append({
            'operator_name': item.operator_name,
            'operator_type': item.operator_type
        })

    GachaConfigData.delete().execute()
    GachaConfigData.insert_data(data)


if __name__ == '__main__':
    transfer_user()
    transfer_admin()
    transfer_replace()
    transfer_intellect()
    transfer_function()
    transfer_disable()
    transfer_pool()
    transfer_gacha_config()
