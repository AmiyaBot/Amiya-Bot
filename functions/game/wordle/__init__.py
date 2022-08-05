import asyncio
import random
import datetime

from core import bot
from core.config import config
from core.database.messages import ReportRecord
from functions.game.wordle.wordleBuilder import *


@bot.on_group_message(function_id='wordle', keywords=['猜字谜', '字谜', '字谜猜猜乐'])
async def _(data: Message):
    if not data.is_group_admin and not data.is_admin:
        return Chain(data).text('抱歉博士，字谜猜猜乐游戏暂时只能由管理员发起哦')

    level = {
        '简单': '简单',
        '困难': '困难'
    }
    level_text = '\n'.join([f'【{lv}】{ct}猜字谜' for lv, ct in level.items()])

    select_level = f'博士，请选择难度：\n\n{level_text}\n\n' \
                   '请回复【难度等级】开始游戏。\n' \
                   '所有群员均可参与游戏，游戏一旦开始，将暂停其他功能的使用哦。如果取消请无视本条消息。\n' \
                   '请回复干员名称参与作答，正确将获得积分，错误将获得提示。\n' \
                   '输入“跳过”或“下一题”将公布答案并跳过本题，输入“结束”或“不玩了”提前结束游戏。\n'

    choice = await data.waiting(Chain(data).text(select_level))

    if not choice:
        return None

    if choice.text not in level.keys():
        return Chain(choice).text('博士，您没有选择难度哦，游戏取消。')

    operators = {}
    referee = WordleReferee()
    curr = None
    level_rate = list(level.keys()).index(choice.text) + 1

    await data.send(Chain(choice).text(f'{choice.text}难度，奖励倍数 {level_rate}'))

    while True:

        if not operators:
            operators = copy.deepcopy(ArknightsGameData().operators)

        operator = operators.pop(random.choice(list(operators.keys())))
        race = ''

        for story in operator.stories():

            if story['story_title'] == '基础档案':
                r = re.search(r'\n【种族】.*?(\S+).*?\n', story['story_text'])

                if r:
                    race = str(r.group(1))

        while not race or not operator.nation or '未知' in race or not operator.drawer_name:
            operator = operators.pop(random.choice(list(operators.keys())))

            for story in operator.stories():

                if story['story_title'] == '基础档案':
                    r = re.search(r'\n【种族】.*?(\S+).*?\n', story['story_text'])

                    if r:
                        race = str(r.group(1))

        if curr != referee.count:
            curr = referee.count
            text = Chain(data, at=False).text(f'题目准备中...（{referee.count + 1}/{wordle_config.questions}）')

            if referee.user_ranking:
                text.text('\n').text(calc_rank(referee)[0], auto_convert=False)

            await data.send(text)
            await asyncio.sleep(2)

        result = await wordle_start(data, operator, choice.text, level_rate)
        end = False
        skip = False

        if result.status in [WordleStatus.userClose, WordleStatus.systemClose]:
            end = True

        if result.status in [WordleStatus.userSkip, WordleStatus.systemSkip]:
            skip = True

        if result.status == WordleStatus.bingo:
            rewards = int(wordle_config.rewards.bingo * level_rate * (100 + result.total_point) / 100)
            UserInfo.add_jade_point(result.answer.user_id, rewards)
            set_rank(referee, result.answer, 1)

        if result.user_point:

            for user_id, point in result.user_point.items():
                set_point(referee, user_id, point)

        if not skip:
            referee.count += 1

            if referee.count >= wordle_config.questions:
                end = True

        if end:
            break

    if referee.count < wordle_config.finish_min:
        return Chain(data, at=False).text(f'游戏结束，本轮共进行了{referee.count}次游戏，不进行结算')

    rewards_rate = (100 + (referee.total_point if referee.total_point > -90 else -90)) / 100
    text, reward_list = calc_rank(referee)
    text += '\n\n'

    for r, l in reward_list.items():

        if r == 0:
            rewards = int(wordle_config.rewards.golden * level_rate * rewards_rate)
            text += f'第一名获得{rewards}合成玉；\n'

        elif r == 1:
            rewards = int(wordle_config.rewards.silver * level_rate * rewards_rate)
            text += f'第二名获得{rewards}合成玉；\n'

        else:
            rewards = int(wordle_config.rewards.copper * level_rate * rewards_rate)
            text += f'第三名获得{rewards}合成玉；\n'

    return Chain(data, at=False).text('游戏结束').text('\n').text(text, auto_convert=False)


@bot.on_group_message(function_id='wordle', keywords=['举报', '举办'])
async def _(data: Message):
    target = data.at_target
    report_id = [item for item in target]
    status = 0 if '清除' in data.text else 1

    if status == 1:

        for i in report_id:

            if i not in config.admin.accounts:

                if data.user_id == i:
                    return Chain(data).text('举报失败！\n您不能举报自己。')

                else:
                    date = datetime.date.today()

                    if ReportRecord.get_or_none(
                        ReportRecord.source_id == data.user_id, ReportRecord.target_id == i, ReportRecord.date == date
                    ) is not None:

                        return Chain(data).text('您今天已经举报过该用户。')

                    else:
                        UserInfo.update(
                            times_report=UserInfo.times_report + 1
                        ).where(
                           UserInfo.user_id == i
                        ).execute()

                        ReportRecord.insert(
                            source_id=data.user_id,
                            target_id=i,
                            date=date
                        ).execute()

                        return Chain(data).text(f'举报{report_id}成功！\n请注意，若恶意举报将可能被永久封禁，请确保您的举报真实有效。')

            else:
                return Chain(data).text('举报失败！\n无法举报管理员。')

    else:
        if data.is_admin:

            for i in report_id:

                UserInfo.update(times_report=0).where(UserInfo.user_id == i).execute()

                return Chain(data).text(f'{report_id}已清除举报。')

        else:
            return None
