import re
import copy

from core import bot, Message, Chain
from core.util import find_similar_list, any_match
from core.resource.arknightsGameData import ArknightsGameData
from core.resource.arknightsGameData.wiki import Wiki

from .operatorInfo import OperatorInfo
from .operatorData import OperatorData
from .initData import InfoInterface, InitData


class LoopBreak(Exception):
    def __init__(self, index, name=''):
        self.index = index
        self.name = name

    def __str__(self):
        return self.index, self.name


def search_info(words: list, source_keys: list = None):
    info_source = {
        'name': [OperatorInfo.operator_map, OperatorInfo.operator_list],
        'level': [InitData.skill_level_list],
        'skill': [OperatorInfo.skill_map],
        'skill_index': [InitData.skill_index_list],
        'skin_key': [OperatorInfo.skins_keywords],
        'voice_key': [InitData.voices],
        'story_key': [OperatorInfo.stories_title]
    }

    info = InfoInterface()
    info_key = list(info_source.keys()) if not source_keys else source_keys

    words = copy.deepcopy(words)

    while True:
        try:
            if len(words) == 0:
                break
            for index, item in enumerate(words):
                for name in copy.deepcopy(info_key):
                    for source in info_source[name]:

                        if name == 'skill':
                            res, rate = find_similar_list(item, source.keys(), _random=True)
                            if res:
                                setattr(info, name, source[res])
                                raise LoopBreak(index, name)

                        elif item in source:
                            value = source[item] if type(source) is dict else item

                            setattr(info, name, value)
                            raise LoopBreak(index, name)

                if index == len(words) - 1:
                    raise LoopBreak('done')
        except LoopBreak as e:
            if e.index == 'done':
                break
            words.pop(e.index)
            info_key.remove(e.name)
            continue

    if info.name and info.skill and OperatorInfo.skill_operator[info.skill] != info.name:
        info.skill = ''

    return info


async def level(data: Message):
    info = search_info(data.text_cut, source_keys=['level'])
    return bool(info.level) or any_match(data.text, ['精英', '专精'])


async def operator(data: Message):
    info = search_info(data.text_cut, source_keys=['name'])
    return bool(info.name)


@bot.on_group_message(function_id='checkOperator', keywords=['模组'])
async def _(data: Message):
    info = search_info(data.text_cut, source_keys=['name'])

    if not info.name:
        wait = await data.waiting(Chain(data).text('博士，请说明需要查询的干员名'))
        if not wait:
            return None
        info.name = wait.text

    result = OperatorData.find_operator_module(info, '故事' in data.text)

    if type(result) is tuple:
        return Chain(data).text_image(*result)
    else:
        return Chain(data).text(result)


@bot.on_group_message(function_id='checkOperator', keywords=['语音'])
async def _(data: Message):
    info = search_info(data.text_cut, source_keys=['voice_key', 'name'])

    if not info.name:
        wait = await data.waiting(Chain(data).text('博士，请说明需要查询的干员名'))
        if not wait:
            return None
        info.name = wait.text

    opt = ArknightsGameData().operators[info.name]
    voices = opt.voices()
    voices_map = {item['voice_title']: item for item in voices}

    if not info.voice_key:

        text = f'博士，这是干员{opt.name}的语音列表\n\n'
        for index, item in enumerate(voices):
            text += f'[{index + 1}] %s\n' % item['voice_title']
        text += '\n回复【序号】查询对应的档案资料'

        wait = await data.waiting(Chain(data).text(text))
        if wait:
            r = re.search(r'(\d+)', wait.text_digits)
            if r:
                index = abs(int(r.group(1))) - 1
                if index >= len(voices):
                    index = len(voices) - 1

                info.voice_key = voices[index]['voice_title']

    if not info.voice_key:
        return None

    if info.voice_key in voices_map:
        text = f'博士，为您找到干员{info.name}的语音档案：\n\n【{info.voice_key}】\n\n' + voices_map[info.voice_key]['voice_text']
        text = text.replace('{@nickname}', data.nickname)

        file = await Wiki.check_exists(opt.wiki_name, info.voice_key)
        if not file:
            await data.send(Chain(data).text(f'正在下载{opt.wiki_name}《{info.voice_key}》语音文件，博士请稍等...'))
            file = await Wiki.download_operator_voices(opt.wiki_name, info.voice_key)
            if not file:
                await data.send(Chain(data).text(f'{opt.wiki_name}《{info.voice_key}》语音文件下载失败...>.<'))

        reply = Chain(data).text(text)
        if file:
            reply.voice(file)

        return reply
    else:
        return Chain(data).text(f'博士，没有找到干员{info.name}《{info.voice_key}》的语音')


@bot.on_group_message(function_id='checkOperator', keywords=['档案', '资料'])
async def _(data: Message):
    info = search_info(data.text_cut, source_keys=['story_key', 'name'])

    if not info.name:
        wait = await data.waiting(Chain(data).text('博士，请说明需要查询的干员名'))
        if not wait:
            return None
        info.name = wait.text

    opt = ArknightsGameData().operators[info.name]
    stories = opt.stories()
    stories_map = {item['story_title']: item['story_text'] for item in stories}

    if not info.story_key:

        text = f'博士，这是干员{opt.name}的档案列表\n\n'
        for index, item in enumerate(stories):
            text += f'[{index + 1}] %s\n' % item['story_title']
        text += '\n回复【序号】查询对应的档案资料'

        wait = await data.waiting(Chain(data).text(text))
        if wait:
            r = re.search(r'(\d+)', wait.text_digits)
            if r:
                index = abs(int(r.group(1))) - 1
                if index >= len(stories):
                    index = len(stories) - 1

                info.story_key = stories[index]['story_title']

    if not info.story_key:
        return None

    if info.story_key in stories_map:
        return Chain(data).text(f'博士，这是干员{info.name}《{info.story_key}》的档案\n\n{stories_map[info.story_key]}')
    else:
        return Chain(data).text(f'博士，没有找到干员{info.name}《{info.story_key}》的档案')


@bot.on_group_message(function_id='checkOperator', verify=level)
async def _(data: Message):
    info = search_info(data.text_cut, source_keys=['level', 'name'])

    if not info.name:
        wait = await data.waiting(Chain(data).text('博士，请说明需要查询的干员名'))
        if not wait:
            return None
        info.name = wait.text

    if not info.level:
        return Chain(data).text('博士，要告诉阿米娅精英或专精等级哦')

    if info.level < 0:
        info.level = abs(info.level)
        result = OperatorData.check_evolve_costs(info)
    else:
        if info.level <= 7 and '材料' in data.text:
            return Chain(data).text('博士，暂时只可以查询专一以上的材料哦')

        elif info.level >= 8 and '材料' in data.text:
            info.level -= 7
            result = OperatorData.check_mastery_costs(info)

        else:
            result = OperatorData.get_skill_data(info)

    if result:
        if type(result) is tuple:
            return Chain(data).text_image(*result)
        else:
            return Chain(data).text(result)


@bot.on_group_message(function_id='checkOperator', verify=operator)
async def _(data: Message):
    info = search_info(data.text_cut, source_keys=['name'])

    result = OperatorData.get_detail_info(info)

    return Chain(data).text_image(*result)
