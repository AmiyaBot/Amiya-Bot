import os
import re
import time
import random
import collections

from core import bot, Message, Chain
from core.database.user import *
from core.database.group import GroupActive
from core.util import read_yaml, TimeRecorder

from .arknights.gacha.gacha import UserGachaInfo

images = []
for root, dirs, files in os.walk('resource/images/face'):
    images += [os.path.join(root, file) for file in files if file != '.gitkeep']

stage = collections.namedtuple('stage', ['feeling', 'text', 'voice'])
touch: List[stage] = read_yaml('config/private/feeling.yaml').touch


@table
class UserInfo(UserBaseModel):
    user_id: str = ForeignKeyField(User, db_column='user_id', on_delete='CASCADE')
    user_feeling: int = IntegerField(default=0)
    user_mood: int = IntegerField(default=15)
    sign_in: int = IntegerField(default=0)
    sign_times: int = IntegerField(default=0)


def sign_in(data: Message, sign_type=0):
    info: UserInfo = UserInfo.get_or_create(user_id=data.user_id)[0]

    if info.sign_in == 0:
        coupon = 50
        feeling = 50

        UserInfo.update(
            sign_in=1,
            user_feeling=UserInfo.user_feeling + feeling,
            sign_times=UserInfo.sign_times + 1
        ).where(UserInfo.user_id == data.user_id).execute()

        UserGachaInfo.get_or_create(user_id=data.user_id)
        UserGachaInfo.update(
            coupon=UserGachaInfo.coupon + coupon
        ).where(UserGachaInfo.user_id == data.user_id).execute()

        return {
            'text': f'{"签到成功，" if sign_type else ""}{coupon}张寻访凭证已经送到博士的办公室啦，请博士注意查收哦',
            'status': True
        }

    if sign_type and info.sign_in == 1:
        return {
            'text': '博士今天已经签到了哦',
            'status': False
        }

    return {
        'text': '',
        'status': False
    }


def talk_time():
    localtime = time.localtime(time.time())
    hours = localtime.tm_hour
    if 0 <= hours <= 5:
        return ''
    elif 5 < hours <= 11:
        return '早上'
    elif 11 < hours <= 14:
        return '中午'
    elif 14 < hours <= 18:
        return '下午'
    elif 18 < hours <= 24:
        return '晚上'


async def check_only_name(data: Message):
    if data.image:
        return False

    text = data.text

    for item in bot.BotHandlers.prefix_keywords:
        if item != '阿米娅' or (item == '阿米娅' and text.startswith(item)):
            text = text.replace(item, '', 1)

    text = re.sub(r'\W', '', text).strip()

    if text == '' or data.is_at:
        return True

    return False


@bot.on_group_message(function_id='user', verify=check_only_name)
async def _(data: Message):
    return Chain(data, quote=False).image(random.choice(images))


@bot.on_group_message(function_id='user', keywords=['阿米驴', '阿驴', '小驴子', '驴子', '驴驴'], check_prefix=False)
async def _(data: Message):
    text = f'哼！Dr.{data.nickname}不许叫人家{random.choice(data.verify.keywords)}，不然人家要生气了！'
    return Chain(data, at=True, quote=False).text(text)


@bot.on_group_message(function_id='user', keywords=['早上好', '早安', '中午好', '午安', '下午好', '晚上好'], check_prefix=False)
async def _(data: Message):
    hour = talk_time()
    text = ''
    if hour:
        text += f'Dr.{data.nickname}，{hour}好～'
    else:
        text += f'Dr.{data.nickname}，这么晚还不睡吗？要注意休息哦～'

    status = sign_in(data)
    if status['status']:
        text += status['text']

    return Chain(data, at=True, quote=False).text(text)


@bot.on_group_message(function_id='user', keywords=['晚安'], check_prefix=False)
async def _(data: Message):
    return Chain(data).text(f'Dr.{data.nickname}，晚安～')


@bot.on_group_message(function_id='user', keywords=['签到'])
async def _(data: Message):
    status = sign_in(data, 1)
    if status:
        return Chain(data).text(status['text'])


@bot.on_group_message(function_id='user', keywords=['信赖', '关系', '好感', '我的信息', '个人信息'])
async def _(data: Message):
    user: UserInfo = UserInfo.get_or_create(user_id=data.user_id)[0]

    feeling = user.user_feeling if user.user_feeling <= 4000 else 4000

    text = '博士，这是您的个人信息\n\n'
    text += f'今日{"已" if user.sign_in else "未"}签到\n'
    text += f'累计签到：{user.sign_times}\n'
    text += f'累计互动：{data.user.message_num}\n'
    text += f'阿米娅的信赖：{int(feeling / 10)}%\n'
    text += f'阿米娅的心情：{int(user.user_mood / 15 * 100)}%\n'

    voice_list = []
    for item in touch:
        if feeling >= item.feeling:
            voice_list.append(item.text)

    if voice_list:
        text += '\n\n' + random.choice(voice_list)

    return Chain(data).text_image(text)


@bot.on_group_message(function_id='admin', keywords=['休息', '下班'])
async def _(data: Message):
    if not data.is_admin and not data.is_group_admin:
        return None

    group_active: GroupActive = GroupActive.get_or_create(group_id=data.group_id)[0]

    if group_active.active == 1:
        GroupActive.update(active=0,
                           sleep_time=int(time.time())).where(GroupActive.group_id == data.group_id).execute()

        return Chain(data).text('打卡下班啦！博士需要的时候再让阿米娅工作吧。^_^')
    else:
        seconds = int(time.time()) - int(group_active.sleep_time)
        total = TimeRecorder.calc_time_total(seconds)

        return Chain(data).text(f'阿米娅休息了{total}，博士需要的时候请让阿米娅工作吧。^_^')


@bot.on_group_message(function_id='admin', keywords=['工作', '上班'])
async def _(data: Message):
    if not data.is_admin and not data.is_group_admin:
        return None

    group_active: GroupActive = GroupActive.get_or_create(group_id=data.group_id)[0]

    if group_active.active == 0:
        seconds = int(time.time()) - int(group_active.sleep_time)
        total = TimeRecorder.calc_time_total(seconds)
        text = '打卡上班啦~阿米娅%s休息了%s……' % ('才' if seconds < 600 else '一共', total)
        if seconds < 600:
            text += '\n博士真是太过分了！哼~ >.<'
        else:
            text += '\n充足的休息才能更好的工作，博士，不要忘记休息哦 ^_^'

        GroupActive.update(active=1, sleep_time=0).where(GroupActive.group_id == data.group_id).execute()
        return Chain(data).text(text)
    else:
        return Chain(data).text('阿米娅没有偷懒哦博士，请您也不要偷懒~')
