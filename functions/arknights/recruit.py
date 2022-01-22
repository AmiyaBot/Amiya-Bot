import dhash
import jieba

from io import BytesIO
from PIL import Image
from jieba import posseg
from typing import List
from itertools import combinations
from core import add_init_task, log, bot, Message, Chain
from core.util import insert_empty, full_match, read_yaml
from core.builtin.baiduCloud import BaiduCloud
from core.network.download import download_async
from core.resource.arknightsGameData import ArknightsGameData

baidu = BaiduCloud()
discern = read_yaml('config/private/recruit.yaml').autoDiscern


def find_operator_tags_by_tags(tags, max_rarity):
    res = []
    for name, item in ArknightsGameData().operators.items():
        if item.is_recruit is False or item.rarity > max_rarity:
            continue
        for tag in item.tags:
            if tag in tags:
                res.append(
                    {
                        'operator_name': name,
                        'operator_rarity': item.rarity,
                        'operator_tags': tag
                    }
                )

    return sorted(res, key=lambda n: -n['operator_rarity'])


def find_combinations(_list):
    result = []
    for i in range(3):
        for n in combinations(_list, i + 1):
            n = list(n)
            if n and not ('高级资深干员' in n and '资深干员' in n):
                result.append(n)
    result.reverse()
    return result


async def auto_discern(data: Message):
    for item in data.image:
        img = await download_async(item)
        if img:
            hash_value = dhash.dhash_int(Image.open(BytesIO(img)))
            diff = dhash.get_num_bits_different(hash_value, discern.templateHash)

            if diff <= discern.maxDifferent:
                data.image = [img]
                return True
    return False


async def get_ocr_result(image):
    res = await baidu.basic_accurate(image)
    if not res:
        res = await baidu.basic_general(image)

    if res and 'words_result' in res:
        return ''.join([item['words'] for item in res['words_result']])


class Recruit:
    tags_list: List[str] = []

    @classmethod
    async def init_tags_list(cls):
        log.info('building operator tags keywords dict...')

        tags = ['资深', '高资', '高级资深']
        for name, item in ArknightsGameData().operators.items():
            for tag in item.tags:
                if tag not in tags:
                    tags.append(tag)

        with open('resource/tags.txt', mode='w+', encoding='utf-8') as file:
            file.write('\n'.join([item + ' 500 n' for item in tags]))

        jieba.load_userdict('resource/tags.txt')

        cls.tags_list = tags

    @classmethod
    async def action(cls, text: str, ocr: bool = False):
        if not text:
            if ocr:
                return '图片识别失败'
            return None

        words = posseg.lcut(text.replace('公招', ''))

        tags = []
        max_rarity = 5
        for item in words:
            if item.word in cls.tags_list:
                if item.word in ['资深', '资深干员'] and '资深干员' not in tags:
                    tags.append('资深干员')
                    continue
                if item.word in ['高资', '高级资深', '高级资深干员'] and '高级资深干员' not in tags:
                    tags.append('高级资深干员')
                    max_rarity = 6
                    continue
                if item.word not in tags:
                    tags.append(item.word)

        if tags:
            result = find_operator_tags_by_tags(tags, max_rarity=max_rarity)
            if result:
                operators = {}
                for item in result:
                    name = item['operator_name']
                    if name not in operators:
                        operators[name] = item
                    else:
                        operators[name]['operator_tags'] += item['operator_tags']

                text = ''
                color = {
                    6: 'FF4343',
                    5: 'FEA63A',
                    4: 'A288B5'
                }

                for comb in [tags] if len(tags) == 1 else find_combinations(tags):
                    lst = []
                    for name, item in operators.items():
                        rarity = item['operator_rarity']
                        if full_match(item['operator_tags'], comb):
                            if rarity == 6 and '高级资深干员' not in comb:
                                continue
                            if rarity >= 4 or rarity == 1:
                                lst.append(item)
                            else:
                                break
                    else:
                        if lst:
                            text += '\n[cl [%s]@#174CC6 cle]\n' % '，'.join(comb)
                            if comb == ['高级资深干员']:
                                text += f'[[cl ★★★★★★@#{color[6]} cle]] 六星 %d 选 1\n' % len(lst)
                                continue
                            if comb == ['资深干员']:
                                text += f'[[cl ★★★★★@#{color[5]} cle]] 五星 %d 选 1\n' % len(lst)
                                continue
                            for item in lst:
                                rarity = item['operator_rarity']
                                name = item["operator_name"]
                                star = '★'
                                c = color[4] if rarity < 5 else color[rarity]
                                text += f'[[cl {insert_empty(star * rarity, 6, True)}@#{c} cle]] {name}\n'

                if text:
                    text = '博士，根据标签已找到以下可以锁定稀有干员的组合\n' + text
                else:
                    text = '博士，没有找到可以锁定稀有干员的组合'

                return text
            else:
                return '博士，无法查询到标签所拥有的稀有干员'

        if ocr:
            return '博士，没有在图片内找到标签信息'


add_init_task(Recruit.init_tags_list)


@bot.on_group_message(function_id='recruit', keywords=['公招', '公开招募'])
async def _(data: Message):
    if data.image:
        # 直接 OCR 识别图片
        return Chain(data).text(
            await Recruit.action(await get_ocr_result(data.image[0]), ocr=True)
        )
    else:
        # 先验证文本内容
        recruit = await Recruit.action(data.text_origin)
        if recruit:
            return Chain(data).text(recruit)
        else:
            # 文本内容验证不出则询问截图
            if not baidu.enable:
                return None

            wait = await data.waiting(Chain(data, at=True, quote=False).text('博士，请发送您的公招界面截图~'))

            if wait and wait.image:
                return Chain(wait).text(
                    await Recruit.action(await get_ocr_result(wait.image[0]), ocr=True)
                )
            else:
                return Chain(data, at=True, quote=False).text('博士，您没有发送图片哦~')


@bot.on_group_message(function_id='recruit', verify=auto_discern, check_prefix=False)
async def _(data: Message):
    return Chain(data).text(
        await Recruit.action(await get_ocr_result(data.image[0]), ocr=True)
    )
