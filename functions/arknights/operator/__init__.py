import re
import time
import copy

from core import bot, Message, Chain
from core.util import find_similar_list, any_match, extract_time, insert_empty
from core.resource.arknightsGameData import ArknightsGameData, ArknightsGameDataResource

from .operatorInfo import OperatorInfo
from .operatorData import OperatorData
from .initData import OperatorSearchInfo, InitData


class LoopBreak(Exception):
    def __init__(self, index, name='', value=''):
        self.index = index
        self.value = value
        self.name = name

    def __str__(self):
        return self.index, self.name


def search_info(words: list, source_keys: list = None, text: str = ''):
    info_source = {
        'name': [OperatorInfo.operator_map, OperatorInfo.operator_list],
        'level': [InitData.skill_level_list],
        'skill': [OperatorInfo.skill_map],
        'skill_index': [InitData.skill_index_list],
        'skin_key': [OperatorInfo.skins_keywords],
        'voice_key': [InitData.voices],
        'story_key': [OperatorInfo.stories_title]
    }

    info = OperatorSearchInfo()
    info_key = list(info_source.keys()) if not source_keys else source_keys

    words = [n.lower() for n in copy.deepcopy(words)]

    if 'name' in info_key and text:
        for name in OperatorInfo.operator_one_char_list:
            if name in text:
                info.name = name

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
                                raise LoopBreak(index, name, source[res])

                        elif item in source:
                            value = source[item] if type(source) is dict else item

                            setattr(info, name, value)
                            raise LoopBreak(index, name, value)

                if index == len(words) - 1:
                    raise LoopBreak('done')
        except LoopBreak as e:
            if e.index == 'done':
                break

            words.pop(e.index)

            if e.name == 'name' and e.value == '阿米娅':
                continue
            else:
                info_key.remove(e.name)

    if info.name == '阿米娅':
        for item in ['阿米娅', 'amiya']:
            t = text.lower()
            if t.startswith(item) and t.count(item) == 1:
                info.name = ''

    if info.name and info.skill and OperatorInfo.skill_operator[info.skill] != info.name:
        info.skill = ''

    return info


async def level_up(data: Message):
    info = search_info(data.text_cut, source_keys=['level', 'skill_index'], text=data.text)
    return bool(info.level) or any_match(data.text, ['精英', '专精']), 2


async def operator(data: Message):
    info = search_info(data.text_cut, source_keys=['name'], text=data.text)
    return bool(info.name), 2 if info.name != '阿米娅' else 0


@bot.on_group_message(function_id='checkOperator', keywords=['皮肤', '立绘'], level=2)
async def _(data: Message):
    info = search_info(data.text_cut, source_keys=['skin_key', 'name'], text=data.text)

    if not info.name:
        wait = await data.waiting(Chain(data).text('博士，请说明需要查询的干员名'))
        if not wait or not wait.text:
            return None
        info.name = wait.text

    operators = ArknightsGameData().operators

    if info.name not in operators:
        return Chain(data).text(f'博士，没有找到干员"{info.name}"')

    opt = operators[info.name]
    skins = opt.skins()

    text = f'博士，这是干员{info.name}的立绘列表\n\n'
    for index, item in enumerate(skins):
        text += f'[{index + 1}] %s\n' % item['skin_name']
    text += '\n回复【序号】查询对应的档案资料'

    wait = await data.waiting(Chain(data).text(text))
    if wait:
        r = re.search(r'(\d+)', wait.text_digits)
        if r:
            index = abs(int(r.group(1))) - 1
            if index >= len(skins):
                index = len(skins) - 1

            skin_item = skins[index]

            text = f'博士，为您找到干员{info.name}的立绘档案：\n\n'
            text += '系列：' + skin_item['skin_group'] + '\n'
            text += '名称：' + skin_item['skin_name'] + '\n'
            text += '获得途径：' + skin_item['skin_source'] + '\n\n'
            text += skin_item['skin_usage'] + '\n'
            text += skin_item['skin_content'] + '\n\n'
            text += skin_item['skin_desc'] + '\n'

            reply = Chain(data).text(text)

            skin_path = await ArknightsGameDataResource.get_skin_file(opt, skin_item)

            if not skin_path:
                reply.text('\n立绘下载失败……')
            else:
                reply.image(skin_path)

            return reply


@bot.on_group_message(function_id='checkOperator', keywords=['模组'], level=2)
async def _(data: Message):
    info = search_info(data.text_cut, source_keys=['name'], text=data.text)

    if not info.name:
        wait = await data.waiting(Chain(data).text('博士，请说明需要查询的干员名'))
        if not wait or not wait.text:
            return None
        info.name = wait.text

    if info.name not in ArknightsGameData().operators:
        return Chain(data).text(f'博士，没有找到干员"{info.name}"')

    if '故事' in data.text:
        result = OperatorData.find_operator_module(info, True)
        return Chain(data).text_image(result)
    else:
        result = OperatorData.find_operator_module(info, False)
        return Chain(data).html('operator/operatorModule.html', result)


@bot.on_group_message(function_id='checkOperator', keywords=['语音'], level=2)
async def _(data: Message):
    info = search_info(data.text_cut, source_keys=['voice_key', 'name'], text=data.text)
    cn = '中文' in data.text

    if not info.name:
        wait = await data.waiting(Chain(data).text('博士，请说明需要查询的干员名'))
        if not wait or not wait.text:
            return None
        info.name = wait.text

    operators = ArknightsGameData().operators

    if info.name not in operators:
        return Chain(data).text(f'博士，没有找到干员"{info.name}"')

    opt = operators[info.name]
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

        reply = Chain(data).text(text)

        file = await ArknightsGameDataResource.get_voice_file(opt, info.voice_key, cn)
        if file:
            reply.voice(file)
        else:
            reply.text(f'{opt.wiki_name}《{info.voice_key}》%s语音文件下载失败...>.<' % ('中文' if cn else '日文'))

        return reply
    else:
        return Chain(data).text(f'博士，没有找到干员{info.name}《{info.voice_key}》的语音')


@bot.on_group_message(function_id='checkOperator', keywords=['档案', '资料'], level=2)
async def _(data: Message):
    info = search_info(data.text_cut, source_keys=['story_key', 'name'], text=data.text)

    if not info.name:
        wait = await data.waiting(Chain(data).text('博士，请说明需要查询的干员名'))
        if not wait or not wait.text:
            return None
        info.name = wait.text

    operators = ArknightsGameData().operators

    if info.name not in operators:
        return Chain(data).text(f'博士，没有找到干员"{info.name}"')

    opt = operators[info.name]
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


@bot.on_group_message(function_id='checkOperator', keywords=['生日'], level=2)
async def _(data: Message):
    date = extract_time(data.text_origin)
    if date:
        if len(date) == 1:
            date.insert(time.localtime(), 0)

        birthday = ArknightsGameData().birthday

        date_str = f'%s到%s期间' % (time.strftime('%Y-%m-%d', date[0]), time.strftime('%Y-%m-%d', date[1]))
        text = f'博士，在{date_str}生日的干员有：\n\n'
        count = 0

        now = time.localtime()

        for month, days in birthday.items():
            if date[0].tm_mon <= month <= date[1].tm_mon:
                for day, items in days.items():
                    if now.tm_mon == month and day < now.tm_mday:
                        continue
                    for item in items:
                        count += 1
                        birth = f'{item.birthday} {item.name}'
                        text += (birth + '\n') if count % 2 == 0 else insert_empty(birth, 15, True)

        return Chain(data).text(text) if count else Chain(data).text(f'博士，{date_str}没有干员生日')

    info = search_info(data.text_cut, source_keys=['name'], text=data.text)

    if not info.name:
        wait = await data.waiting(Chain(data).text('博士，请说明需要查询的干员名'))
        if not wait or not wait.text:
            return None
        info.name = wait.text

    operators = ArknightsGameData().operators

    if info.name not in operators:
        return Chain(data).text(f'博士，没有找到干员"{info.name}"')

    opt = operators[info.name]

    return Chain(data).text(f'博士，干员{opt.name}的生日是{opt.birthday}')


@bot.on_group_message(function_id='checkOperator', verify=level_up)
async def _(data: Message):
    info = search_info(data.text_cut, source_keys=['level', 'skill_index', 'name'], text=data.text)

    if not info.name:
        wait = await data.waiting(Chain(data).text('博士，请说明需要查询的干员名'))
        if not wait or not wait.text:
            return None
        info.name = wait.text

    if '材料' in data.text:
        result = await OperatorData.get_level_up_cost(info)
        template = 'operator/operatorCost.html'
    else:
        result = await OperatorData.get_skills_detail(info)
        template = 'operator/skillsDetail.html'

    if not result:
        return Chain(data).text('博士，请仔细描述想要查询的信息哦')

    return Chain(data).html(template, result)


@bot.on_group_message(function_id='checkOperator', verify=operator)
async def _(data: Message):
    info = search_info(data.text_cut, source_keys=['name'], text=data.text)

    if '技能' in data.text:
        result = await OperatorData.get_skills_detail(info)
        template = 'operator/skillsDetail.html'
    else:
        result = await OperatorData.get_operator_detail(info)
        template = 'operator/operatorInfo.html'

    if not result:
        return Chain(data).text('博士，请仔细描述想要查询的信息哦')

    return Chain(data).html(template, result)
