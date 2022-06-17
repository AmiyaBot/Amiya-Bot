import os
import random

from io import BytesIO
from PIL import Image
from typing import Dict, Union
from operator import itemgetter
from itertools import groupby
from dataclasses import dataclass, field
from core.util import any_match, random_pop, read_yaml
from core.resource.arknightsGameData import ArknightsGameData, ArknightsGameDataResource, Operator
from core import Message, Chain

guess_config = read_yaml('config/private/game.yaml').guess
nations_config = read_yaml('config/private/game.yaml').nations

class GuessStatus:
    systemSkip = 0
    userSkip = 1
    bingo = 2
    userClose = 3
    systemClose = 4


@dataclass
class GuessResult:
    status: int = GuessStatus.systemSkip
    answer: Message = None
    user_point: Dict[int, int] = field(default_factory=dict)
    total_point: int = 0


@dataclass
class GuessReferee:
    count: int = 0
    user_num: int = 0
    user_point: Dict[int, int] = field(default_factory=dict)
    user_ranking: Dict[int, dict] = field(default_factory=dict)
    total_point: int = 0


def set_point(cls: Union[GuessResult, GuessReferee], user_id: int, point: int):
    if user_id not in cls.user_point:
        cls.user_point[user_id] = point
    else:
        cls.user_point[user_id] += point
    cls.total_point += point


def set_rank(cls: GuessReferee, answer: Message, point: int):
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


def calc_rank(cls: GuessReferee):
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
    for points, items in group:
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


async def guess_start(data: Message, operator: Operator, level: str, title: str, level_rate: int):
    ask = Chain(data, at=False).text(f'博士，这是哪位干员的{title}呢，请发送干员名猜一猜吧！').text('\n')

    if level == '初级':
        skin = random.choice(operator.skins())
        skin_path = await ArknightsGameDataResource.get_skin_file(operator, skin)

        if not skin_path:
            await data.send(Chain(data, at=False).text('非常抱歉博士，立绘下载失败。本次游戏结束~[face:9]'))
            return GuessResult(GuessStatus.systemClose)
        else:
            img = Image.open(skin_path)

            area_size = int(img.size[0] * 0.2)
            padding = 200

            position_x = random.randint(padding, img.size[0] - area_size - padding)
            position_y = random.randint(padding, img.size[1] - area_size - padding)

            container = BytesIO()
            region = img.crop((position_x, position_y, position_x + area_size, position_y + area_size))
            region.save(container, format='PNG')

            ask.image(container.getvalue())

    if level == '中级':
        skills = operator.skills()[0]

        if not skills:
            return GuessResult()

        skill = random.choice(skills)

        if any_match(skill['skill_name'], ['α', 'β', 'γ']):
            return GuessResult()

        skill_icon = 'resource/gamedata/skill/%s.png' % skill['skill_icon']

        if not os.path.exists(skill_icon):
            return GuessResult()

        ask.image(skill_icon)

    if level == '高级':
        voices = operator.voices()
        if not voices:
            return GuessResult()

        voice = random.choice(voices)
        voice_path = await ArknightsGameDataResource.get_voice_file(operator, voice['voice_title'])

        ask.text('\n\n语音：').text(voice['voice_text'].replace(operator.name, 'XXX'))

        if not voice_path:
            await data.send(Chain(data, at=False).text('非常抱歉博士，语音文件下载失败。本次游戏结束~[face:9]'))
            return GuessResult(GuessStatus.systemClose)
        else:
            ask.voice(voice_path)

    if level == '资深':
        stories = operator.stories()
        if not stories:
            return GuessResult()

        stories = [n for n in stories if n['story_title'] not in ['基础档案', '综合体检测试', '综合性能检测结果', '临床诊断分析']]
        story = random.choice(stories)['story_text'].replace(operator.name, 'XXX')
        section = story.split('。')

        if len(section) >= 5:
            start = random.randint(0, len(section) - 5)
            story = '。'.join(section[start:start + 5])

        ask.text(story, auto_convert=False)

    await data.send(ask)
    
    building_skill = operator.building_skills
    tips = [
        f'TA是{operator.rarity}星干员',
        # f'TA的职业是{operator.classes}',
        f'TA的子职业是{operator.classes_sub}',
        f'TA的标签是%s' % ','.join(operator.tags),
        # f'TA%s可以公招获得' % ('不' if not operator.is_recruit else ''),
        f'TA的英文名首字母是大写的{operator.en_name[0]}'
        
    ]
    if operator.nation:
        nation_name = nations_config[operator.nation]
        tips.append(f'TA的阵营是{nation_name[0]}')
    if operator.drawer_name:
        tips.append(f'TA的画师是{operator.drawer_name}')
    # if len(operator.name) > 1:
    #     tips.append(f'TA的代号里有一个字是"{random.choice(operator.name)}"')
    if operator.limit:
        tips.append('TA是限定干员')

    result = GuessResult()
    count = 0
    max_count = 10

    while True:
        answer = await data.waiting(force=True, target='group', max_time=60)

        if not answer:
            await data.send(Chain(data, at=False).text(f'答案是{operator.name}，没有博士回答吗？那游戏结束咯~'))
            result.status = GuessStatus.systemClose
            return result

        if any_match(answer.text, ['下一题', '放弃', '跳过']):
            await data.send(Chain(data, at=False).text(f'答案是{operator.name}，结算奖励-10%'))
            set_point(result, answer.user_id, -10)
            result.answer = answer
            result.status = GuessStatus.userSkip
            return result

        if any_match(answer.text, ['不知道', '提示']):
            if tips:
                text = f'{answer.nickname} 使用了提示，结算奖励-2%'
                await data.send(Chain(data, at=False).text(text).text('\n').text(random_pop(tips)))
                set_point(result, answer.user_id, -2)
            else:
                await data.send(Chain(data, at=False).text('没有更多提示了~'))
            continue

        if any_match(answer.text, ['不玩了', '结束']):
            await data.send(Chain(answer, at=False).text(f'答案是{operator.name}，游戏结束~'))
            result.status = GuessStatus.userClose
            return result

        if answer.text not in ArknightsGameData().operators.keys():
            continue

        if answer.text == operator.index_name:
            rewards = int(guess_config.rewards.bingo * level_rate * (100 + result.total_point) / 100)

            await data.send(Chain(answer, at=False).text(f'回答正确！分数+1，合成玉+{rewards}'))
            
            result.answer = answer
            result.status = GuessStatus.bingo
            return result
        else:
            count += 1
            if count >= max_count:
                await data.send(Chain(data, at=False).text(f'机会耗尽，答案是{operator.name}，结算奖励-5%'))
                set_point(result, 0, -5)
                return result
            else:
                await data.send(Chain(answer, at=False).text(f'不对哦，博士。请再猜猜吧~（{count}/{max_count}）'))
