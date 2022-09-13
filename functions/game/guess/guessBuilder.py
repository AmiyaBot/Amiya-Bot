from typing import Dict
from operator import itemgetter
from itertools import groupby
from dataclasses import dataclass, field
from amiyabot.builtin.message import ChannelMessagesItem
from core import Message


class GameState:
    systemSkip = 0
    userSkip = 1
    bingo = 2
    userClose = 3
    systemClose = 4


@dataclass
class RateCalculator:
    user_rate: Dict[str, int] = field(default_factory=dict)
    total_rate: int = 0

    def set_rate(self, user_id: str, rate: int):
        if user_id not in self.user_rate:
            self.user_rate[user_id] = rate
        else:
            self.user_rate[user_id] += rate
        self.total_rate += rate


@dataclass
class GuessUser:
    user_id: str
    nickname: str
    index: int
    point: int
    max_combo: int = 1

    def __getitem__(self, item):
        return getattr(self, item)


@dataclass
class GuessResult(RateCalculator):
    answer: Message = None
    state: int = GameState.systemSkip

    point: int = 0
    rewards: int = 0

    user_rate: Dict[str, int] = field(default_factory=dict)
    total_rate: int = 0

    event: ChannelMessagesItem = None


@dataclass
class GuessReferee(RateCalculator):
    round: int = 0
    combo_user: str = ''
    combo_count: int = 0
    user_num: int = 0
    user_ranking: Dict[str, GuessUser] = field(default_factory=dict)
    user_rate: Dict[str, int] = field(default_factory=dict)
    total_rate: int = 0

    def set_rank(self, answer: Message, point: int):
        user_id = answer.user_id

        if user_id not in self.user_ranking:
            self.user_num += 1
            self.user_ranking[user_id] = GuessUser(**{
                'user_id': user_id,
                'nickname': answer.nickname,
                'index': self.user_num,
                'point': point
            })
        else:
            self.user_ranking[user_id].point += point

    def calc_rank(self):
        sorted_list = sorted(list(self.user_ranking.values()), key=lambda n: n.point, reverse=True)
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
        for points, items in group:
            if group_index in group_index_map:
                text += f'\n{group_index_map[group_index]}：\n'
            elif no_rank:
                no_rank = False
                text += '\n未上榜：\n'

            for item in items:
                if group_index in reward_list:
                    reward_list[group_index].append(item.user_id)
                text += f' -- {item.nickname} （{item.point}分）最高连击{item.max_combo}\n'

            group_index += 1

        return text, reward_list
