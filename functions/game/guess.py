import os
import random
import asyncio

from core import bot, Message, Chain
from core.resource.arknightsGameData import ArknightsGameData, ArknightsGameDataResource
from core.util import any_match, random_pop


async def guess_start(data: Message, level: str, title: str):
    operators = ArknightsGameData().operators
    operator = operators[random.choice(list(operators.keys()))]

    question = Chain(data, quote=False).text(f'博士，这是哪位干员的{title}呢，请发送干员名猜一猜吧！').text('\n')

    if level == '初级':
        skin = random.choice(operator.skins())
        skin_path = await ArknightsGameDataResource.get_skin_file(operator, skin)

        if not skin_path:
            await data.send(Chain(data, quote=False).text('非常抱歉博士，立绘下载失败。本次游戏结束~[face:9]'))
            return False
        else:
            question.image(skin_path)

    if level == '中级':
        skill = random.choice(operator.skills()[0])

        if any_match(skill['skill_name'], ['α', 'β', 'γ']):
            return True

        skill_icon = 'resource/images/skill/%s.png' % skill['skill_icon']

        if not os.path.exists(skill_icon):
            return True

        question.image(skill_icon)

    if level == '高级':
        voices = operator.voices()
        if not voices:
            return True

        voice = random.choice(voices)
        voice_path = await ArknightsGameDataResource.get_voice_file(operator, voice['voice_title'])

        question.text('\n\n语音：').text(voice['voice_text'])

        if not voice_path:
            await data.send(Chain(data, quote=False).text('非常抱歉博士，语音文件下载失败。本次游戏结束~[face:9]'))
            return False
        else:
            question.voice(voice_path)

    if level == '资深':
        stories = operator.stories()
        if not stories:
            return True

        stories = [n for n in stories if n['story_title'] not in ['基础档案', '综合体检测试']]
        story = random.choice(stories)['story_text'].replace(operator.name, 'XXX')
        section = story.split('。')

        if len(section) >= 5:
            start = random.randint(0, len(section) - 5)
            story = '。'.join(section[start:start + 5])

        question.text_image(story)

    await data.send(question)

    tips = [
        f'TA是{operator.rarity}星干员',
        f'TA的职业是{operator.classes}',
        f'TA的分支职业是{operator.classes_sub}',
        f'TA的[cl 攻击范围@#ff0000 cle]是\n\n{operator.range}',
        f'TA的标签是%s' % ','.join(operator.tags)
    ]
    if len(operator.name) > 1:
        tips.append(f'TA的名字里有一个字是"{random.choice(operator.name)}"')
    if operator.limit:
        tips.append('TA是限定干员')

    while True:
        answer = await data.waiting(force=True, target='group', max_time=60)

        if not answer:
            await data.send(Chain(data, quote=False).text(f'答案是{operator.name}，没有博士回答吗？那游戏结束咯~'))
            return False

        if any_match(answer.text, ['下一题', '放弃', '跳过']):
            await data.send(Chain(data, quote=False).text(f'答案是{operator.name}'))
            break

        if any_match(answer.text, ['不知道', '提示']):
            if tips:
                await data.send(Chain(data, quote=False).text(random_pop(tips)))
            else:
                await data.send(Chain(data, quote=False).text('没有更多提示了~'))
            continue

        if any_match(answer.text, ['不玩了', '结束']):
            await data.send(Chain(answer).text(f'答案是{operator.name}，游戏结束~'))
            return False

        if answer.text not in operators.keys():
            continue

        if answer.text == operator.index_name:
            await data.send(Chain(answer).text('恭喜博士答对啦！'))
            break
        else:
            await data.send(Chain(answer).text('不对哦，博士。请再猜猜吧~'))

    return True


@bot.on_group_message(function_id='guess', keywords=['猜干员'])
async def _(data: Message):
    if not data.is_group_admin:
        return Chain(data).text('抱歉博士，猜干员游戏暂时只能由管理员发起哦')

    level = {
        '初级': '立绘',
        '中级': '技能图标',
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
        return Chain(choice).text('博士，您没有选择难度哦。游戏取消。')

    while True:
        await data.send(Chain(data, quote=False).text('题目准备中...'))
        await asyncio.sleep(2)
        if not await guess_start(data, choice.text, level[choice.text]):
            break
