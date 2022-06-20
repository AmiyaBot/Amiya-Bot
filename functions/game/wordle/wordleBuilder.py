import copy
import re

from dataclasses import dataclass, field
from itertools import groupby
from operator import itemgetter
from typing import Dict, Union

from core import Message, Chain
from core.database.user import UserInfo
from core.resource.arknightsGameData import ArknightsGameData, Operator
from core.util import any_match, read_yaml

wordle_config = read_yaml('config/private/game.yaml').wordle
nations_config = read_yaml('config/private/game.yaml').nations


class WordleStatus:
    systemSkip = 0
    userSkip = 1
    bingo = 2
    userClose = 3
    systemClose = 4


@dataclass
class WordleResult:
    status: int = WordleStatus.systemSkip
    answer: Message = None
    user_point: Dict[int, int] = field(default_factory=dict)
    total_point: int = 0


@dataclass
class WordleReferee:
    count: int = 0
    user_num: int = 0
    user_point: Dict[int, int] = field(default_factory=dict)
    user_ranking: Dict[int, dict] = field(default_factory=dict)
    total_point: int = 0


def set_point(cls: Union[WordleResult, WordleReferee], user_id: int, point: int):
    if user_id not in cls.user_point:
        cls.user_point[user_id] = point
    else:
        cls.user_point[user_id] += point
    cls.total_point += point


def set_rank(cls: WordleReferee, answer: Message, point: int):
    user_id = int(answer.user_id)

    if user_id not in cls.user_ranking:
        cls.user_num += 1
        cls.user_ranking[user_id] = {
            'user_id': user_id,
            'nickname': answer.nickname,
            'index': cls.user_num,
            'point': point
        }
    else:
        cls.user_ranking[user_id]['point'] += point


def calc_rank(cls: WordleReferee):
    sorted_list = sorted(list(cls.user_ranking.values()), key=lambda n: n['point'], reverse=True)
    group = groupby(sorted_list, itemgetter('point'))
    group_index = 0
    group_index_map = {
        0: '第一名',
        1: '第二名',
        2: '第三名'
    }
    reward_list = {
        0: [],
        1: [],
        2: []
    }

    text = '排行榜：\n'
    no_rank = True

    for wordle, items in group:

        if group_index in group_index_map:
            text += f'\n{group_index_map[group_index]}：\n'

        elif no_rank:
            no_rank = False
            text += '\n未上榜：\n'

        for item in items:

            if group_index in reward_list:
                reward_list[group_index].append(item['user_id'])
            text += ' -- {nickname} （{point}分）\n'.format(nickname=item['nickname'], point=item['point'])

        group_index += 1

    return text, reward_list


async def wordle_start(data: Message, operator: Operator, level: str, level_rate: int):
    rarity_ans = 'XXX'
    classes_ans = 'XXX'
    classes_sub_ans = 'XXX'
    nation_ans = 'XXX'
    race_ans = 'XXX'
    drawer_ans = 'XXX'
    match = 0
    ans_list = '目前猜过的干员有：'
    ans_names = []

    if level == '简单':
        max_count = 12
    else:
        max_count = 8

    text = [
        '博士，快来猜猜这是谁吧！',
        f'（{level}模式共有{max_count}次猜测机会）',
        '',
        f'稀有度：{rarity_ans}星',
        f'职业：{classes_ans}',
        f'子职业：{classes_sub_ans}',
        f'阵营：{nation_ans}',
        f'种族：{race_ans}',
        f'画师：{drawer_ans}',
    ]
    ask = Chain(data, at=False).text('\n'.join(text), auto_convert=False)
    result = WordleResult()
    count = 0
    race = ''

    await data.send(ask)

    for story in operator.stories():

        if story['story_title'] == '基础档案':
            r = re.search(r'\n【种族】.*?(\S+).*?\n', story['story_text'])

            if r:
                race = str(r.group(1))

                if race == '卡特斯/奇美拉':
                    race = '卡特斯'

    while True:
        answer = await data.waiting(force=True, target='group', max_time=120)
        race_guess = ''

        if not answer:
            await data.send(Chain(data, at=False).text(f'答案是{operator.name}，没有博士回答吗？那游戏结束咯~'))
            result.status = WordleStatus.systemClose
            return result

        times_report = UserInfo.get_or_none(UserInfo.user_id == answer.user_id)

        if times_report is None:
            continue

        if any_match(answer.text, ['下一题', '跳过']):
            await data.send(Chain(data, at=False).text(f'答案是{operator.name}，结算奖励-10%'))
            set_point(result, answer.user_id, -10)
            result.answer = answer
            result.status = WordleStatus.userSkip
            return result

        if any_match(answer.text, ['不玩了', '结束']):
            await data.send(Chain(answer, at=False).text(f'答案是{operator.name}，游戏结束~'))
            result.status = WordleStatus.userClose
            return result

        if answer.text in ans_names:

            if times_report.times_report > wordle_config.report.times:

                if level_rate >= wordle_config.report.level:
                    await data.send(Chain(data, at=False).text(f'您被举报的次数过多，不允许参与该难度游戏，请联系管理员。'))

                    continue

            await data.send(Chain(answer, at=False).text(f'博士，{answer.text}已经被猜过了，换个干员试试吧~'))
            continue

        if answer.text not in ArknightsGameData().operators.keys():
            continue

        if answer.text == operator.index_name:

            if times_report.times_report > wordle_config.report.times:

                if level_rate >= wordle_config.report.level:
                    await data.send(Chain(data, at=False).text(f'您被举报的次数过多，不允许参与该难度游戏，请联系管理员。'))

                    continue

            rewards = int(wordle_config.rewards.bingo * level_rate * (100 + result.total_point) / 100)

            await data.send(Chain(answer, at=False).text(f'回答正确！分数+1，合成玉+{rewards}'))

            result.answer = answer
            result.status = WordleStatus.bingo
            return result
        else:

            if times_report.times_report > wordle_config.report.times:

                if level_rate >= wordle_config.report.level:
                    await data.send(Chain(data, at=False).text(f'您被举报的次数过多，不允许参与该难度游戏，请联系管理员。'))

                    continue

            count += 1
            if count >= max_count:
                await data.send(Chain(data, at=False).text(f'机会耗尽，答案是{operator.name}，结算奖励-5%'))
                set_point(result, 0, -5)
                return result
            else:
                operator_list = copy.deepcopy(ArknightsGameData().operators)
                operator_guess = operator_list.pop(answer.text)

                for story in operator_guess.stories():

                    if story['story_title'] == '基础档案':
                        r = re.search(r'\n【种族】.*?(\S+).*?\n', story['story_text'])

                        if r:
                            race_guess = str(r.group(1))

                            if race_guess == '卡特斯/奇美拉':
                                race_guess = '卡特斯'

                if operator.rarity == operator_guess.rarity and rarity_ans == 'XXX':
                    match = match + 1
                    rarity_ans = operator.rarity

                if operator.classes == operator_guess.classes and classes_ans == 'XXX':
                    match = match + 1
                    classes_ans = operator.classes

                if operator.classes_sub == operator_guess.classes_sub and classes_sub_ans == 'XXX':
                    match = match + 1
                    classes_sub_ans = operator.classes_sub

                if operator.nation == operator_guess.nation and nation_ans == 'XXX':
                    match = match + 1
                    nation_ans = nations_config[operator.nation][0]

                if race == race_guess and race_ans == 'XXX':
                    match = match + 1
                    race_ans = race_guess

                if operator.drawer_name == operator_guess.drawer_name and drawer_ans == 'XXX':
                    match = match + 1
                    drawer_ans = operator.drawer_name

                if match == 1 or match == 2:
                    reply_text = '博士的猜测离答案不远了~'

                elif match == 3 or match == 4:
                    reply_text = '博士的猜测离答案非常接近了~'

                elif match == 5 or match == 6:
                    reply_text = '博士！就快要猜对了哦！'

                else:
                    reply_text = '博士，所有的线索都对不上哦~'

                ans_list += ' ' + answer.text
                ans_names.append(answer.text)
                text = [
                    f'{reply_text}（{count}/{max_count}）',
                    f'稀有度：{rarity_ans}星',
                    f'职业：{classes_ans}',
                    f'子职业：{classes_sub_ans}',
                    f'阵营：{nation_ans}',
                    f'种族：{race_ans}',
                    f'画师：{drawer_ans}',
                    f'{ans_list}',
                ]
                await data.send(Chain(answer, at=False).text('\n'.join(text), auto_convert=False))
