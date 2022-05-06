import copy
import asyncio

from core import bot
from core.database.user import UserInfo
from functions.game.guess.guessBuilder import *


@bot.on_group_message(function_id='guess', keywords=['猜干员'])
async def _(data: Message):
    if not data.is_group_admin and not data.is_admin:
        return Chain(data).text('抱歉博士，猜干员游戏暂时只能由管理员发起哦')

    level = {
        '初级': '立绘',
        '中级': '技能',
        '高级': '语音',
        '资深': '档案'
    }
    level_text = '\n'.join([f'【{lv}】{ct}猜干员' for lv, ct in level.items()])

    select_level = f'博士，请选择难度：\n\n{level_text}\n\n' \
                   '请回复【难度等级】开始游戏。\n' \
                   '所有群员均可参与竞猜，游戏一旦开始，将暂停其他功能的使用哦。如果取消请无视本条消息。\n' \
                   '详细说明请查看功能菜单'

    choice = await data.waiting(Chain(data).text(select_level))

    if not choice:
        return None

    if choice.text not in level.keys():
        return Chain(choice).text('博士，您没有选择难度哦，游戏取消。')

    operators = {}
    referee = GuessReferee()
    curr = None
    level_rate = list(level.keys()).index(choice.text) + 1

    await data.send(Chain(choice).text(f'{choice.text}难度，奖励倍数 {level_rate}'))

    while True:
        if not operators:
            operators = copy.deepcopy(ArknightsGameData().operators)

        operator = operators.pop(random.choice(list(operators.keys())))

        if curr != referee.count:
            curr = referee.count

            text = Chain(data, at=False).text(f'题目准备中...（{referee.count + 1}/{guess_config.questions}）')
            if referee.user_ranking:
                text.text('\n').text(calc_rank(referee)[0], auto_convert=False)

            await data.send(text)
            await asyncio.sleep(2)

        result = await guess_start(data, operator, choice.text, level[choice.text], level_rate)
        end = False
        skip = False

        if result.status in [GuessStatus.userClose, GuessStatus.systemClose]:
            end = True
        if result.status in [GuessStatus.userSkip, GuessStatus.systemSkip]:
            skip = True
        if result.status == GuessStatus.bingo:
            rewards = int(guess_config.rewards.bingo * level_rate * (100 + result.total_point) / 100)
            UserInfo.add_jade_point(result.answer.user_id, rewards)
            set_rank(referee, result.answer, 1)

        if result.user_point:
            for user_id, point in result.user_point.items():
                set_point(referee, user_id, point)

        if not skip:
            referee.count += 1
            if referee.count >= guess_config.questions:
                end = True

        if end:
            break

    if referee.count < guess_config.finish_min:
        return Chain(data, at=False).text(f'游戏结束，本轮共进行了{referee.count}次竞猜，不进行结算')

    rewards_rate = (100 + (referee.total_point if referee.total_point > -90 else -90)) / 100
    text, reward_list = calc_rank(referee)
    text += '\n\n'

    for r, l in reward_list.items():
        if r == 0:
            rewards = int(guess_config.rewards.golden * level_rate * rewards_rate)
            text += f'第一名获得{rewards}合成玉；\n'
        elif r == 1:
            rewards = int(guess_config.rewards.silver * level_rate * rewards_rate)
            text += f'第二名获得{rewards}合成玉；\n'
        else:
            rewards = int(guess_config.rewards.copper * level_rate * rewards_rate)
            text += f'第三名获得{rewards}合成玉；\n'

    return Chain(data, at=False).text('游戏结束').text('\n').text(text, auto_convert=False)
