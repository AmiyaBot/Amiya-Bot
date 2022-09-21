import os
import dhash
import jieba
import asyncio

from io import BytesIO
from PIL import Image
from jieba import posseg
from typing import List
from itertools import combinations
from amiyabot import PluginInstance
from amiyabot.network.download import download_async

from core import log, Message, Chain
from core.util import all_match, read_yaml, extract_zip_plugin
from core.lib.baiduCloud import BaiduCloud
from core.resource.arknightsGameData import ArknightsGameData

curr_dir = os.path.dirname(__file__)
recruit_plugin = 'resource/plugins/recruit'

if curr_dir.endswith('.zip'):
    extract_zip_plugin(curr_dir, recruit_plugin)
else:
    recruit_plugin = curr_dir

baidu = BaiduCloud(read_yaml(f'{recruit_plugin}/baiduCloud.yaml'))
recruit_config = read_yaml(f'{recruit_plugin}/recruit.yaml')
discern = recruit_config.autoDiscern


class Recruit:
    tags_list: List[str] = []

    @staticmethod
    async def init_tags_list():
        log.info('building operator tags keywords dict...')

        tags = ['资深', '高资', '高级资深']
        for name, item in ArknightsGameData.operators.items():
            for tag in item.tags:
                if tag not in tags:
                    tags.append(tag)

        with open(f'{recruit_plugin}/tags.txt', mode='w+', encoding='utf-8') as file:
            file.write('\n'.join([item + ' 500 n' for item in tags]))

        jieba.load_userdict(f'{recruit_plugin}/tags.txt')

        Recruit.tags_list = tags

    @classmethod
    async def action(cls, data: Message, text: str, ocr: bool = False):
        reply = Chain(data)

        if not text:
            if ocr:
                return reply.text('图片识别失败')
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

                groups = []

                for comb in [tags] if len(tags) == 1 else find_combinations(tags):
                    lst = []
                    max_r = 0
                    for name, item in operators.items():
                        rarity = item['operator_rarity']
                        if all_match(item['operator_tags'], comb):
                            if rarity == 6 and '高级资深干员' not in comb:
                                continue
                            if rarity >= 4 or rarity == 1:
                                if rarity > max_r:
                                    max_r = rarity
                                lst.append(item)
                            else:
                                break
                    else:
                        if lst:
                            groups.append({
                                'tags': comb,
                                'max_rarity': max_r,
                                'operators': lst
                            })

                if groups:
                    groups = sorted(groups, key=lambda n: (-len(n['tags']), -n['max_rarity']))
                    return reply.html('template/operator/operatorRecruit.html', {'groups': groups, 'tags': tags})
                else:
                    return reply.text('博士，没有找到可以锁定稀有干员的组合')
            else:
                return reply.text('博士，无法查询到标签所拥有的稀有干员')

        if ocr:
            return reply.text('博士，没有在图内找到标签信息')


class RecruitPluginInstance(PluginInstance):
    def install(self):
        asyncio.create_task(Recruit.init_tags_list())


bot = RecruitPluginInstance(
    name='明日方舟公招查询',
    version='1.0',
    plugin_id='amiyabot-arknights-recruit',
    plugin_type='official',
    description='可通过指令或图像识别规划公招标签组合',
    document=f'{recruit_plugin}/README.md'
)


def find_operator_tags_by_tags(tags, max_rarity):
    res = []
    for name, item in ArknightsGameData.operators.items():
        if not item.is_recruit or item.rarity > max_rarity:
            continue
        for tag in item.tags:
            if tag in tags:
                res.append(
                    {
                        'operator_id': item.id,
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
            try:
                hash_value = dhash.dhash_int(Image.open(BytesIO(img)))
                diff = dhash.get_num_bits_different(hash_value, discern.templateHash)
            except OSError:
                return False

            if diff <= discern.maxDifferent:
                data.image = [img]
                return True
    return False


async def get_ocr_result(image):
    if baidu.enable:
        res = await baidu.basic_accurate(image)
        if not res:
            res = await baidu.basic_general(image)

        if res and 'words_result' in res:
            return ''.join([item['words'] for item in res['words_result']])

    return ''


@bot.on_message(keywords=['公招', '公开招募'], allow_direct=True, level=10)
async def _(data: Message):
    if data.image:
        # 直接 OCR 识别图片
        return await Recruit.action(data, await get_ocr_result(data.image[0]), ocr=True)
    else:
        # 先验证文本内容
        recruit = await Recruit.action(data, data.text_origin)
        if recruit:
            return recruit
        else:
            # 文本内容验证不出则询问截图
            if not baidu.enable:
                return None

            wait = await data.wait(Chain(data, at=True).text('博士，请发送您的公招界面截图~'), force=True)

            if wait and wait.image:
                return await Recruit.action(wait, await get_ocr_result(wait.image[0]), ocr=True)
            else:
                return Chain(data, at=True).text('博士，您没有发送图片哦~')


@bot.on_message(verify=auto_discern, check_prefix=False, allow_direct=True)
async def _(data: Message):
    return await Recruit.action(data, await get_ocr_result(data.image[0]), ocr=True)
