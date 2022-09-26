import os
import random

from io import BytesIO
from PIL import Image
from core.util import any_match, random_pop, read_yaml
from core.resource.arknightsGameData import ArknightsGameData, ArknightsGameDataResource, Operator
from core import Chain

from .guessBuilder import *

curr_dir = os.path.dirname(__file__)

game_config = read_yaml(f'{curr_dir}/guess.yaml')
guess_config = game_config.guess
guess_keyword = game_config.keyword


async def guess_filter(data: Message):
    return data.text in [
        *guess_keyword.skip,
        *guess_keyword.tips,
        *guess_keyword.over,
        *ArknightsGameData.operators.keys()
    ]


async def guess_start(referee: GuessReferee,
                      data: Message,
                      operator: Operator,
                      title: str,
                      level: str,
                      level_rate: int):
    ask = Chain(data, at=False)

    if referee.round == 1:
        ask.text(f'博士，这是哪位干员的{title}呢，请发送干员名猜一猜吧！').text('\n')

    if level == '初级':
        skin = random.choice(operator.skins())
        skin_path = await ArknightsGameDataResource.get_skin_file(skin)

        if not skin_path:
            return GuessResult(answer=data, state=GameState.systemSkip)
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
            return GuessResult(answer=data)

        skill = random.choice(skills)

        if any_match(skill['skill_name'], ['α', 'β', 'γ', '急救']):
            return GuessResult(answer=data)

        skill_icon = 'resource/gamedata/skill/%s.png' % skill['skill_icon']

        if not os.path.exists(skill_icon):
            return GuessResult(answer=data)

        ask.image(skill_icon)

    if level == '高级':
        await data.send(Chain(data, at=False, reference=True).text('抱歉博士，语音模块暂未开放，请选择其他难度'))
        return GuessResult(answer=data, state=GameState.systemClose)

        # voices = operator.voices()
        # if not voices:
        #     return GuessResult(data)
        #
        # voice = random.choice(voices)
        # voice_path = await ArknightsGameDataResource.get_voice_file(operator, voice['voice_title'])
        #
        # ask.text('\n\n语音：').text(voice['voice_text'].replace(operator.name, 'XXX'))
        #
        # if not voice_path:
        #     await data.send(Chain(data, at=False).text('非常抱歉博士，语音文件下载失败。本次游戏结束~[face:9]'))
        #     return GuessResult(data, GuessStatus.systemClose)
        # else:
        #     ask.voice(voice_path)

    if level == '资深':
        stories = operator.stories()
        if not stories:
            return GuessResult(answer=data)

        stories = [n for n in stories if n['story_title'] not in ['基础档案', '综合体检测试', '综合性能检测结果', '临床诊断分析']]
        story = random.choice(stories)['story_text'].replace(operator.name, 'XXX')
        section = story.split('。')

        if len(section) >= 5:
            start = random.randint(0, len(section) - 5)
            story = '。'.join(section[start:start + 5])

        ask.text(story, auto_convert=False)

    tips = [
        f'TA是{operator.rarity}星干员',
        f'TA的职业是{operator.classes}',
        f'TA的分支职业是{operator.classes_sub}',
        f'TA的标签是%s' % ','.join(operator.tags)
    ]
    if len(operator.name) > 1:
        tips.append(f'TA的代号里有一个字是"{random.choice(operator.name)}"')
    if operator.limit:
        tips.append('TA是限定干员')

    result = GuessResult(answer=data)
    count = 0
    max_count = 10

    # 开始竞猜
    while True:
        event = await data.wait_channel(ask,
                                        force=True,
                                        clean=bool(ask),
                                        max_time=60,
                                        data_filter=guess_filter)

        ask = None
        result.event = event

        # 超时没人回答，游戏结束
        if not event:
            await data.send(Chain(data, at=False).text(f'答案是{operator.name}，没有博士回答吗？那游戏结束咯~'))
            result.state = GameState.systemClose
            return result

        result.answer = answer = event.message

        # 跳过问题
        if answer.text in guess_keyword.skip:
            await data.send(Chain(answer, at=False, reference=True).text(f'答案是{operator.name}，结算奖励-5%'))
            result.set_rate(answer.user_id, -5)
            result.state = GameState.userSkip
            return result

        # 获取提示
        if answer.text in guess_keyword.tips:
            if tips:
                text = f'{answer.nickname} 使用了提示，结算奖励-2%'
                await data.send(Chain(answer, at=False, reference=True).text(text).text('\n').text(random_pop(tips)))
                result.set_rate(answer.user_id, -2)
            else:
                await data.send(Chain(answer, at=False, reference=True).text('没有更多提示了~'))
            continue

        # 手动结束游戏
        if answer.text in guess_keyword.over:
            await data.send(Chain(answer, at=False, reference=True).text(f'答案是{operator.name}，游戏结束~'))
            result.state = GameState.userClose
            return result

        # 回答问题
        if answer.text == operator.index_name:
            # 回答正确
            rewards = int(guess_config.rewards.bingo * level_rate * (100 + result.total_rate) / 100)
            point = 1

            combo_text = ''

            if referee.combo_user != answer.user_id:
                if referee.combo_count >= 3:
                    # 终结连击，+ 1 分
                    point += 1
                    combo_text = '终结连击！'

                # 开始记录连击
                referee.combo_user = answer.user_id
                referee.combo_count = 1
            else:
                # 连击 + 1
                referee.combo_count += 1
                if referee.combo_count > referee.user_ranking[answer.user_id].max_combo:
                    referee.user_ranking[answer.user_id].max_combo = referee.combo_count

            # 3 连击以上，每 3 个连击数 + 1 分、合成玉 + 10%
            if referee.combo_count > 1:
                point += int(referee.combo_count / 3)
                rewards = int(rewards * (1 + int(referee.combo_count / 3) * 0.1))

                combo_text = f'{referee.combo_count}连击！'

            reply = Chain(answer, at=False, reference=True).text(f'回答正确！{combo_text}分数+{point}，合成玉+{rewards}')
            await data.send(reply)

            result.point = point
            result.answer = answer
            result.state = GameState.bingo
            result.rewards = rewards
            return result
        else:
            reply = Chain(answer, at=False, reference=True)
            reduce = 1

            # 连击中断
            if referee.combo_user == answer.user_id:
                if referee.combo_count:
                    reduce = referee.combo_count
                    if reduce > 1:
                        reply.text('连击中断！')
                referee.combo_count = 0

            # 答错扣分
            # referee.set_rank(answer, -reduce)

            count += 1
            if count >= max_count:
                await data.send(reply.text(f'机会耗尽，答案是{operator.name}，结算奖励-5%'))
                result.set_rate('0', -5)
                return result
            else:
                await data.send(reply.text(f'答案不正确。请再猜猜吧~（{count}/{max_count}）'))
