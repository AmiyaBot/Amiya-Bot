import random

from core import bot, Message, Chain
from core.resource.arknightsGameData import ArknightsGameData, ArknightsGameDataResource
from core.util import any_match, random_pop


async def guess_start(data: Message, level: str):
    operators = ArknightsGameData().operators
    operator = operators[random.choice(list(operators.keys()))]

    question = Chain(data, quote=False).text('博士，这是哪位干员的资料呢，请发送干员名猜一猜吧！（回答时间60秒）')

    if level == '初级':
        skin = random.choice(operator.skins())
        skin_path = await ArknightsGameDataResource.get_skin_file(operator, skin)

        if not skin_path:
            await data.send(Chain(data, quote=False).text('非常抱歉博士，立绘下载失败。本次游戏结束~[face:9]'))
            return False
        else:
            question.image(skin_path)

    if level == '中级':
        voice = random.choice(operator.voices())
        voice_path = await ArknightsGameDataResource.get_vioce_file(operator, voice['voice_title'])

        question.text('\n\n语音：').text(voice['voice_text'])

        if not voice_path:
            await data.send(Chain(data, quote=False).text('非常抱歉博士，语音文件下载失败。本次游戏结束~[face:9]'))
            return False
        else:
            question.voice(voice_path)

    if level == '高级':
        stories = operator.stories()
        if not stories:
            return None

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

        if any_match(answer.text, ['下一题', '放弃']):
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

        if answer.text == operator.name:
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
        '中级': '语音',
        '高级': '档案'
    }
    level_text = '\n'.join([f'【{lv}】{ct}猜干员' for lv, ct in level.items()])

    select_level = f'博士，请选择难度：\n\n{level_text}\n\n' \
                   '请回复【难度等级】开始游戏。\n所有群员均可参与竞猜，游戏一旦开始，将暂停其他功能的使用哦。如果取消请无视本条消息。'

    choice = await data.waiting(Chain(data).text(select_level))

    if choice.text not in ['初级', '中级', '高级']:
        return Chain(choice).text('博士，您没有选择难度哦。游戏取消。')

    keep_gaming = True
    while keep_gaming:
        keep_gaming = await guess_start(data, choice.text)
