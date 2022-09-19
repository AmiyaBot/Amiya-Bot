import os
import re
import time
import base64
import random
import zipfile

from amiyabot.network.download import download_async
from amiyabot import GroupConfig, PluginInstance

from core import send_to_console_channel, tasks_control, Message, Chain, Equal
from core.util import read_yaml, check_sentence_by_re, any_match, create_dir
from core.database.bot import Admin
from core.database.user import User, UserInfo, UserGachaInfo
from core.resource.arknightsGameData.penguin import save_penguin_data

curr_dir = os.path.dirname(__file__)
resource_path = 'resource/plugins/user'

if curr_dir.endswith('.zip'):
    create_dir(resource_path)
    pack = zipfile.ZipFile(curr_dir)
    for pack_file in pack.namelist():
        if pack_file.endswith('.py'):
            continue
        pack.extract(pack_file, resource_path)
else:
    resource_path = curr_dir

talking = read_yaml(f'{resource_path}/talking.yaml')
bot = PluginInstance(
    name='用户模块',
    version='1.0',
    plugin_id='amiyabot-user'
)
bot.set_group_config(GroupConfig('user', allow_direct=True))


def get_face():
    images = []
    for root, dirs, files in os.walk(f'{resource_path}/face'):
        images += [os.path.join(root, file) for file in files if file != '.gitkeep']

    return images


def sign_in(data: Message, sign_type=0):
    info: UserInfo = UserInfo.get_user(data.user_id)

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


def compose_talk_verify(words, names):
    async def verify(data: Message):
        return check_sentence_by_re(data.text, words, names)

    return verify


async def user_info(data: Message):
    avatar = await download_async(data.avatar)
    image = 'data:image/jpg;base64,' + base64.b64encode(avatar).decode('ascii')

    info = {
        'avatar': image,
        'nickname': data.nickname,
        **UserInfo.get_user_info(data.user_id)
    }

    return Chain(data).html(f'{resource_path}/template/userInfo.html', info, width=700, height=300)


async def only_name(data: Message):
    if data.image:
        return False

    text = data.text

    for item in bot.prefix_keywords:
        if item != '阿米娅' or (item == '阿米娅' and text.startswith(item)):
            text = text.replace(item, '', 1)

    text = re.sub(r'\W', '', text).strip()

    return text == '', 2


async def reset():
    UserInfo.update(sign_in=0, user_mood=15, jade_point_max=0).execute()

    await save_penguin_data()
    await send_to_console_channel(
        Chain().text(f'维护完成：%s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    )


@bot.on_message(group_id='user', verify=only_name)
async def _(data: Message):
    return Chain(data, at=False).image(random.choice(get_face()))


@bot.on_message(group_id='user', verify=compose_talk_verify(talking.talk.positive, talking.call.positive))
async def _(data: Message):
    user: UserInfo = UserInfo.get_user(data.user_id)
    reply = Chain(data)

    if user.user_mood == 0:
        text = '阿米娅这次就原谅博士吧，博士要好好对阿米娅哦[face:21]'
    else:
        text = random.choice(talking.touch)

    setattr(reply, 'feeling', 5)
    return reply.text(text, auto_convert=False)


@bot.on_message(group_id='user', verify=compose_talk_verify(talking.talk.inactive, talking.call.positive))
async def _(data: Message):
    user: UserInfo = UserInfo.get_user(data.user_id)
    reply = Chain(data)
    setattr(reply, 'feeling', -5)

    if user.user_mood - 5 <= 0:
        return reply.text('(阿米娅没有应答...似乎已经生气了...)')

    anger = int((1 - (user.user_mood - 5 if user.user_mood - 5 >= 0 else 0) / 15) * 100)

    return reply.text(f'博士为什么要说这种话，阿米娅要生气了！[face:67]（怒气值：{anger}%）')


@bot.on_message(group_id='user', keywords=list(talking.call.inactive), check_prefix=False)
async def _(data: Message):
    bad_word = any_match(data.text, list(talking.call.inactive))
    text = f'哼！Dr. {data.nickname}不许叫人家{bad_word}，不然人家要生气了！'

    reply = Chain(data).text(text)
    setattr(reply, 'feeling', -5)

    return reply


@bot.on_message(group_id='user', keywords=['早上好', '早安', '中午好', '午安', '下午好', '晚上好'])
async def _(data: Message):
    hour = talk_time()
    text = ''
    if hour:
        text += f'Dr. {data.nickname}，{hour}好～'
    else:
        text += f'Dr. {data.nickname}，这么晚还不睡吗？要注意休息哦～'

    status = sign_in(data)
    if status['status']:
        text += status['text']

    return Chain(data).text(text)


@bot.on_message(group_id='user', keywords=['晚安'])
async def _(data: Message):
    return Chain(data).text(f'Dr. {data.nickname}，晚安～')


@bot.on_message(group_id='user', keywords=['我错了', '对不起', '抱歉'])
async def _(data: Message):
    info: UserInfo = UserInfo.get_user(data.user_id)

    reply = Chain(data)
    setattr(reply, 'feeling', 5)

    if not info or info.user_mood >= 15:
        return reply.text('博士为什么要这么说呢，嗯……博士是不是偷偷做了对不起阿米娅的事[face:181]')
    else:
        return reply.text('好吧，阿米娅就当博士刚刚是在开玩笑吧，博士要好好对阿米娅哦[face:21]')


@bot.on_message(group_id='user', keywords=['签到'])
async def _(data: Message):
    status = sign_in(data, 1)

    reply = await user_info(data)

    return reply.text(status['text'])


@bot.on_message(group_id='user', keywords=['信赖', '关系', '好感', '我的信息', '个人信息'])
async def _(data: Message):
    return await user_info(data)


@bot.on_message(group_id='user', keywords=Equal('手动维护'))
async def _(data: Message):
    if Admin.get_or_none(account=data.user_id):
        await reset()


@bot.before_bot_reply
async def _(data: Message):
    user: UserInfo = UserInfo.get_user(data.user_id)

    if user.user_id.black == 1:
        return False

    if user.user_mood <= 0 and not any_match(data.text, ['我错了', '对不起', '抱歉']):
        await data.send(Chain(data).text('哼~阿米娅生气了！不理博士！[face:38]'))
        return False
    return True


@bot.after_bot_reply
async def _(data: Chain):
    user_id = data.data.user_id
    feeling = 2

    if not User.get_or_none(user_id=user_id):
        return None

    if hasattr(data, 'feeling'):
        feeling = getattr(data, 'feeling')

    user: UserInfo = UserInfo.get_user(user_id)

    user_mood = user.user_mood + feeling
    if user_mood <= 0:
        user_mood = 0
    if user_mood >= 15:
        user_mood = 15

    User.update(
        nickname=data.data.nickname,
        message_num=User.message_num + 1
    ).where(User.user_id == user_id).execute()

    UserInfo.update(
        user_mood=user_mood,
        user_feeling=UserInfo.user_feeling + feeling,
    ).where(UserInfo.user_id == user_id).execute()


@tasks_control.timed_task(each=60)
async def _():
    now = time.localtime(time.time())
    hour = now.tm_hour
    mint = now.tm_min

    if hour == 4 and mint == 0:
        await reset()
