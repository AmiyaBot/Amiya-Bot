import jieba

from jieba import posseg
from itertools import combinations

from core import Message, Chain, AmiyaBot
from core.util import log
from core.util.config import config
from core.util.common import all_item_in_text, insert_empty
from core.util.baiduCloud import OpticalCharacterRecognition
from core.database.models import User
from dataSource import DataSource, Operator

from handlers.constraint import FuncInterface


class Recruit(FuncInterface):
    def __init__(self, data_source: DataSource, bot: AmiyaBot):
        super().__init__(function_id='recruit')

        self.ocr = OpticalCharacterRecognition(config.baiduCloud)

        self.bot = bot
        self.data = data_source
        self.tags = []

        self.init_tags_list()

        jieba.load_userdict('resource/tags.txt')

    def init_tags_list(self):
        log.info('building operator\'s tags keywords dict...')

        tags = ['资深', '高资', '高级资深']
        for name, item in self.data.operators.items():
            for tag in item.tags:
                if tag not in tags:
                    tags.append(tag)

        self.tags = tags

        with open('resource/tags.txt', mode='w+', encoding='utf-8') as file:
            file.write('\n'.join([item + ' 500 n' for item in tags]))

    @FuncInterface.is_disable
    def check(self, data: Message):
        for item in ['公招', '公开招募'] + self.tags:
            if item in data.text:
                return True
        return False

    @FuncInterface.is_used
    def action(self, data: Message):

        # 符合条件将直接进行图像识别
        if data.image and data.image != 'RecruitORC' and self.ocr.enable:
            self.update_status(data, False)

            self.bot.send_message(Chain(data).text('图片识别中，博士请稍等...'))

            # 优先尝试精准识别，若失败，则使用普通识别
            res = self.ocr.basic_accurate(data.image)
            if not res:
                res = self.ocr.basic_general(data.image)

            # 覆盖原有的消息，用图像识别的结果进行查询
            if res and 'words_result' in res:
                data.text = ''.join([item['words'] for item in res['words_result']])
            data.image = 'RecruitORC'

        words = posseg.lcut(
            data.text.replace('公招', '')
        )

        tags = []
        max_rarity = 5
        for item in words:
            if item.word in self.tags:
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
            result = self.find_operator_tags_by_tags(tags, max_rarity=max_rarity)
            if result:
                operators = {}
                for item in result:
                    name = item['operator_name']
                    if name not in operators:
                        operators[name] = item
                    else:
                        operators[name]['operator_tags'] += item['operator_tags']

                text = ''
                for comb in [tags] if len(tags) == 1 else self.find_combinations(tags):
                    lst = []
                    for name, item in operators.items():
                        rarity = item['operator_rarity']
                        if all_item_in_text(item['operator_tags'], comb):
                            if rarity == 6 and '高级资深干员' not in comb:
                                continue
                            if rarity >= 4 or rarity == 1:
                                lst.append(item)
                            else:
                                break
                    else:
                        if lst:
                            text += '\n[%s]\n' % '，'.join(comb)
                            if comb == ['高级资深干员']:
                                text += '[★★★★★★] 六星 %d 选 1\n' % len(lst)
                                continue
                            if comb == ['资深干员']:
                                text += '[★★★★★　] 五星 %d 选 1\n' % len(lst)
                                continue
                            for item in lst:
                                rarity = item['operator_rarity']
                                star = '☆' if rarity < 5 else '★'
                                text += '[%s] %s\n' % (insert_empty(star * rarity, 6, True), item['operator_name'])

                if text:
                    text = '博士，根据标签已找到以下可以锁定稀有干员的组合\n' + text
                else:
                    text = '博士，没有找到可以锁定稀有干员的组合'

                return Chain(data, quote=data.image == 'RecruitORC').text(text)
            else:
                return Chain(data, quote=data.image == 'RecruitORC').text('博士，无法查询到标签所拥有的的干员')
        else:
            # 如果无法匹配标签，但 image 为 RecruitORC，则代表这是图片识别后的结果
            if data.image == 'RecruitORC':
                return Chain(data, quote=True).text('博士，没有在图片内找到标签信息')

            # 如果 image 为空，则可以等待发图后使用图像识别继续
            if data.image == '' and self.ocr.enable:
                self.update_status(data, True)
                return Chain(data).text('博士，请发送您的公招界面截图~')

    def find_operator_tags_by_tags(self, tags, max_rarity):
        res = []
        for name, item in self.data.operators.items():
            item: Operator
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

    @staticmethod
    def update_status(data: Message, status: bool):
        User.update(waiting='Recruit' if status else '').where(User.user_id == data.user_id).execute()

    @staticmethod
    def find_combinations(_list):
        result = []
        for i in range(3):
            for n in combinations(_list, i + 1):
                n = list(n)
                if n and not ('高级资深干员' in n and '资深干员' in n):
                    result.append(n)
        result.reverse()
        return result
