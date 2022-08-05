import os
import re
import time
import random

from core import bot, websocket, http, account, custom_chain, Message, Chain, Mirai
from core.database.user import User, UserInfo, UserGachaInfo, game
from core.database.group import check_group_active
from core.database.messages import MessageRecord
from core.builtin.baiduCloud import BaiduCloud
from core.util import read_yaml, check_sentence_by_re

from functions.arknights.gacha.box import get_user_gacha_detail

baidu = BaiduCloud()
talking = read_yaml('config/private/talking.yaml')


def get_face():
    images = []
    for root, dirs, files in os.walk('resource/images/face'):
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


async def only_name(data: Message):
    if data.image:
        return False

    text = data.text

    for item in bot.BotHandlers.prefix_keywords:
        if item != '阿米娅' or (item == '阿米娅' and text.startswith(item)):
            text = text.replace(item, '', 1)

    text = re.sub(r'\W', '', text).strip()

    return text == '', 2


async def any_talk(data: Message):
    return True, 0


async def maintain():
    UserInfo.update(sign_in=0, user_mood=15, jade_point_max=0).execute()

    last_time = int(time.time()) - 7 * 86400
    MessageRecord.delete().where(MessageRecord.create_time <= last_time).execute()

    async with websocket.send_to_admin() as chain:
        chain.text(f'维护完成：%s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))


@bot.on_private_message(keywords=bot.equal('维护'))
async def _(data: Message):
    if data.is_admin:
        await maintain()


@bot.on_group_message(function_id='user', verify=only_name)
async def _(data: Message):
    return Chain(data, at=False).image(random.choice(get_face()))


@bot.on_group_message(function_id='user', verify=any_talk)
async def _(data: Message):
    result = await baidu.emotion(data.text_initial)
    if result and 'items' in result and result['items']:
        item = result['items'][0]
        label = item['label']
        text = ''

        if label == 'neutral':
            pass
        elif label == 'optimistic':
            text = '虽然听不懂博士在说什么，但阿米娅能感受到博士现在高兴的心情，欸嘿嘿……'
        elif label == 'pessimistic':
            text = '博士心情不好吗？阿米娅不懂怎么安慰博士，但阿米娅会默默陪在博士身边的'

        if 'replies' in item and item['replies']:
            text = random.choice(item['replies'])

        if text:
            return Chain(data).text(text)


@bot.on_group_message(function_id='user', verify=compose_talk_verify(talking.talk.positive, talking.call.positive))
async def _(data: Message):
    user: UserInfo = UserInfo.get_user(data.user_id)
    reply = Chain(data)

    if user.user_mood == 0:
        text = '阿米娅这次就原谅博士吧，博士要好好对阿米娅哦[face:21]'
    else:
        text = random.choice(talking.touch)

    setattr(reply, 'feeling', 5)
    return reply.text(text, auto_convert=False)


@bot.on_group_message(function_id='user', verify=compose_talk_verify(talking.talk.inactive, talking.call.positive))
async def _(data: Message):
    user: UserInfo = UserInfo.get_user(data.user_id)
    reply = Chain(data)
    setattr(reply, 'feeling', -5)

    if user.user_mood - 5 <= 0:
        return reply.text('(阿米娅没有应答...似乎已经生气了...)')

    anger = int((1 - (user.user_mood - 5 if user.user_mood - 5 >= 0 else 0) / 15) * 100)

    return reply.text(f'博士为什么要说这种话，阿米娅要生气了！[face:67]（怒气值：{anger}%）')


@bot.on_group_message(function_id='user', keywords=list(talking.call.inactive), check_prefix=False)
async def _(data: Message):
    text = f'哼！Dr.{data.nickname}不许叫人家{random.choice(data.verify.keywords)}，不然人家要生气了！'

    reply = Chain(data, at=True).text(text)
    setattr(reply, 'feeling', -5)

    return reply


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

    return Chain(data, at=True).text(text)


@bot.on_group_message(function_id='user', keywords=['晚安'], check_prefix=False)
async def _(data: Message):
    return Chain(data).text(f'Dr.{data.nickname}，晚安～')


@bot.on_group_message(function_id='user', keywords=['我错了', '对不起', '抱歉'])
async def _(data: Message):
    info: UserInfo = UserInfo.get_user(data.user_id)

    reply = Chain(data)
    setattr(reply, 'feeling', 5)

    if not info or info.user_mood >= 15:
        return reply.text('博士为什么要这么说呢，嗯……博士是不是偷偷做了对不起阿米娅的事[face:181]')
    else:
        return reply.text('好吧，阿米娅就当博士刚刚是在开玩笑吧，博士要好好对阿米娅哦[face:21]')


@bot.on_group_message(function_id='user', keywords=['签到'])
async def _(data: Message):
    status = sign_in(data, 1)
    if status:
        return Chain(data).text(status['text'])


@bot.on_group_message(function_id='user', keywords=['信赖', '关系', '好感', '我的信息', '个人信息'])
async def _(data: Message):
    user: UserInfo = UserInfo.get_user(data.user_id)

    feeling = user.user_feeling if user.user_feeling <= 4000 else 4000

    text = '博士，这是您的个人信息\n\n'
    text += f'今日{"已" if user.sign_in else "未"}签到\n'
    text += f'累计签到：{user.sign_times}\n'
    text += f'累计互动：{data.user.message_num}\n'
    text += f'阿米娅的信赖：{int(feeling / 10)}%\n'
    text += f'阿米娅的心情：{int(user.user_mood / 15 * 100)}%\n\n'

    text += f'合成玉：{user.jade_point}\n'
    text += f'今日已获得：{user.jade_point_max}/{game.jade_point_max}\n'
    text += f'猜字谜被举报次数：{user.times_report}\n\n'

    gacha = get_user_gacha_detail(data.user_id)
    if gacha:
        text += f'累计抽卡数：%s\n' % gacha['count']
        text += f'BOX干员数：%s\n' % gacha['box_num']
        text += f'  --  6星干员数：%s (平均概率 %s)\n' % tuple(gacha['rarity_6'])
        text += f'  --  5星干员数：%s (平均概率 %s)\n' % tuple(gacha['rarity_5'])
        text += f'  --  4星干员数：%s (平均概率 %s)\n' % tuple(gacha['rarity_4'])
        text += f'  --  3星干员数：%s (平均概率 %s)\n' % tuple(gacha['rarity_3'])

    voice_list = []
    for item in talking.stage:
        if feeling >= item.feeling:
            voice_list.append(item.text)

    if voice_list:
        text += '\n\n' + random.choice(voice_list)

    return Chain(data).text_image(text)


@bot.on_event(Mirai.GroupRecallEvent)
async def _(data: Mirai.GroupRecallEvent):
    # todo 暂停撤回响应功能
    #
    # if random.randint(1, 10) == 1:
    #     return False
    #
    # if not check_group_active(data.operator.group.id):
    #     return False
    #
    # chain = custom_chain(data.operator.id, data.operator.group.id)
    # await websocket.send(chain.at(enter=False).text(f'哼~撤回也没用，阿米娅已经看见了！[face:269]'))
    pass


@bot.on_event(Mirai.MemberJoinEvent)
async def _(data: Mirai.MemberJoinEvent):
    if not check_group_active(data.member.group.id):
        return False

    chain = custom_chain(data.member.id, data.member.group.id)
    await websocket.send_message(chain.text(f'欢迎新博士{data.member.memberName}~，我是阿米娅，请多多指教哦~\n提示：发送【阿米娅功能】来获取帮助。'))


@bot.on_event(Mirai.BotJoinGroupEvent)
async def _(data: Mirai.BotJoinGroupEvent):
    chain = custom_chain(group_id=data.group.id)
    await websocket.send_message(chain.text('博士，初次见面，这里是阿米娅，请大家多多指教哦~\n提示：发送【阿米娅功能】来获取帮助。'))


@bot.on_event(Mirai.NudgeEvent)
async def _(data: Mirai.NudgeEvent):
    if data.fromId == account or data.target != account:
        return False

    if not check_group_active(data.subject.id):
        return False

    user: User = User.get_or_none(user_id=data.fromId)
    if user and user.black == 1:
        return False

    if random.randint(1, 10) > 5:
        await http.send_nudge(data.fromId, data.subject.id)
    else:
        return custom_chain(data.fromId, data.subject.id).image(random.choice(get_face()))


@bot.before_bot_reply
async def _(data: Message):
    user: UserInfo = UserInfo.get_user(data.user_id)
    if user.user_mood <= 0:
        await websocket.send_message(
            custom_chain(data.user_id, data.group_id, data.type).at(enter=True).text('哼~阿米娅生气了！不理博士！[face:38]'))
        return False
    return True


@bot.after_bot_reply
async def _(data: Chain):
    if data.command == 'sendGroupMessage':
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
            message_num=User.message_num + 1
        ).where(User.user_id == user_id).execute()
        UserInfo.update(
            user_mood=user_mood,
            user_feeling=UserInfo.user_feeling + feeling,
        ).where(UserInfo.user_id == user_id).execute()


@bot.timed_task(each=60)
async def _():
    now = time.localtime(time.time())
    hour = now.tm_hour
    mint = now.tm_min

    if hour == 4 and mint == 0:
        await maintain()
