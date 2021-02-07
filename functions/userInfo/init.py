import random

from database.baseController import BaseController
from message.messageType import TextImage
from modules.commonMethods import Reply
from functions.gacha.gacha import GaCha

database = BaseController()

touch = [
    {
        "feeling": 4000,
        "text": "博士……我最近……是不是变得有点不像自己？那些偶然升起的无名怒火……是我的吗？就算这样，不，就算这样我也不会放弃。我会保护你的，博士，凭这把剑。",
        "voice": "阿米娅(近卫)_信赖提升后交谈3"
    },
    {
        "feeling": 3000,
        "text": "就算是现在，我也偶尔会想起米莎的眼神，想起霜星的怒吼，想起爱国者的嘶鸣……Ace、Scout以及许多干员为一个信念牺牲了自己。可大地上那么多的感染者，又是为了什么而死？",
        "voice": "阿米娅(近卫)_信赖提升后交谈2"
    },
    {
        "feeling": 2400,
        "text": "死亡应该铭刻在我们的记忆里，永不遗忘，无论这死亡是谁带来的，又是被带给了谁。我们的错误永远不会变成正确……那些疤痕应该要一直提醒我们，警告我们有多脆弱。",
        "voice": "阿米娅(近卫)_信赖提升后交谈1"
    },
    {
        "feeling": 2000,
        "text": "博士，我们的脚下，是一条漫长的道路……也许这是一次没有终点的旅行，但如果是和您一起，我觉得，非常幸福。",
        "voice": "阿米娅_信赖提升后交谈3"
    },
    {
        "feeling": 1000,
        "text": "嘿嘿，博士，悄悄告诉你一件事……我重新开始练小提琴了。是想在这次派对上给大家的惊喜，所以博士……要对大家保密哦",
        "voice": "阿米娅_信赖提升后交谈2"
    },
    {
        "feeling": 400,
        "text": "有时候，我会想起寒冷的家乡，那里就连空气中都弥漫着铜锈的味道。相比之下罗德岛是如此的温暖。所以，为了守护好这里，我必须更加努力才行。",
        "voice": "阿米娅_信赖提升后交谈1"
    },
    {
        "feeling": 0,
        "text": "博士，您工作辛苦了",
        "voice": "阿米娅_任命助理"
    }
]


class Init:
    def __init__(self):
        self.function_id = 'userInfo'
        self.keyword = ['信赖', '关系', '好感', '我的信息', '个人信息']

    def action(self, data):
        user = database.user.get_user(data['user_id'])
        if user:
            feeling = user['user_feeling'] if user['user_feeling'] <= 4000 else 4000

            gc = GaCha(data['user_id'])

            text = '博士，这是您的个人信息\n\n' \
                   '今日{sign}签到\n' \
                   '累计签到：{sign_times}\n' \
                   '累计互动：{message_num}\n' \
                   '阿米娅的信赖：{feeling}%\n' \
                   '阿米娅的心情：{mood}%\n' \
                   '\n【抽卡信息】\n' \
                   '寻访凭证剩余：{coupon}\n' \
                   '{break_even}' \
                .format(sign='已' if user['sign_in'] else '未',
                        sign_times=user['sign_times'],
                        message_num=user['message_num'],
                        feeling=int(feeling / 10),
                        mood=int(user['user_mood'] / 15 * 100),
                        coupon=user['coupon'],
                        break_even=gc.check_break_even())

            voice_list = []
            for item in touch:
                if feeling >= item['feeling']:
                    voice_list.append(item['text'])

            if voice_list:
                text += '\n\n' + random.choice(voice_list)

            return Reply(TextImage(text))
        else:
            database.user.update_user(data['user_id'], 0)
            return self.action(data)
