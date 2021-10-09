from peewee import *

sqlite_db = SqliteDatabase('amiya.db',
                           pragmas={
                               'timeout': 30
                           },
                           check_same_thread=False)


class BaseModel(Model):
    class Meta:
        database = sqlite_db


class User(BaseModel):
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


class Admin(BaseModel):
    user_id = TextField(primary_key=True)
    password = TextField()
    last_login = BigIntegerField(null=True)
    last_login_ip = TextField(null=True)
    active = IntegerField(default=1)


class AdminTraceLog(BaseModel):
    log_id = IntegerField(primary_key=True, constraints=[SQL('autoincrement')])
    user_id = TextField()
    interface = TextField()
    methods = TextField()
    params = TextField()
    time = BigIntegerField()


class Group(BaseModel):
    group_id = TextField(primary_key=True)
    group_name = TextField()
    permission = TextField()


class GroupActive(BaseModel):
    group_id = TextField(primary_key=True)
    active = IntegerField(default=1)
    sleep_time = BigIntegerField(default=0)


class GroupSetting(BaseModel):
    group_id = TextField(primary_key=True)
    send_notice = IntegerField(default=0)
    send_weibo = IntegerField(default=0)


class GroupNotice(BaseModel):
    notice_id = IntegerField(primary_key=True, constraints=[SQL('autoincrement')])
    content = TextField()
    send_time = BigIntegerField()
    send_user = TextField()


class Upload(BaseModel):
    path = TextField(primary_key=True)
    type = TextField()
    mirai_id = TextField()


class Message(BaseModel):
    user_id = IntegerField()
    target_id = IntegerField(null=True)
    group_id = IntegerField(null=True)
    record = TextField(null=True)
    msg_type = TextField()
    msg_time = IntegerField()


class Function(BaseModel):
    function_id = TextField(primary_key=True)
    use_num = IntegerField(default=1)


class Disable(BaseModel):
    group_id = TextField()
    function_id = TextField()
    status = IntegerField()


class Pool(BaseModel):
    pool_id = IntegerField(primary_key=True, constraints=[SQL('autoincrement')])
    pool_name = TextField(unique=True)
    pickup_6 = TextField(null=True)
    pickup_5 = TextField(null=True)
    pickup_4 = TextField(null=True)
    pickup_s = TextField(null=True)
    limit_pool = IntegerField()


class PoolSpOperator(BaseModel):
    sp_id = IntegerField(primary_key=True, constraints=[SQL('autoincrement')])
    pool_id = IntegerField()
    operator_name = TextField()
    rarity = IntegerField()
    classes = TextField()
    image = TextField()


class GachaConfig(BaseModel):
    conf_id = IntegerField(primary_key=True, constraints=[SQL('autoincrement')])
    operator_name = TextField()
    operator_type = IntegerField()


class Intellect(BaseModel):
    user_id = TextField(primary_key=True)
    cur_num = IntegerField()
    full_num = IntegerField()
    full_time = BigIntegerField()
    message_type = TextField()
    group_id = TextField()
    in_time = BigIntegerField()
    status = IntegerField()
