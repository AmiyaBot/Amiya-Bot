import jieba

from jieba import posseg
from itertools import combinations
from modules.commonMethods import Reply, all_item_in_text, insert_empty
from database.baseController import BaseController

print('loading tags data...')
database = BaseController()
tags_file = database.operator.create_tags_file()
jieba.load_userdict(tags_file)


class Init:
    def __init__(self):
        self.function_id = 'recruit'
        self.keyword = ['公招', '公开招募']
        self.tags = []
        with open(tags_file, encoding='utf-8') as tags:
            for item in tags.read().split('\n'):
                self.tags.append(item.split(' ')[0].strip())

    def action(self, data, end=False):

        message = data['text']
        user_id = data['user_id']

        msg_words = posseg.lcut(
            message.replace('公招', '')
        )

        tags = []
        max_rarity = 5
        for item in msg_words:
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
            result = database.operator.find_operator_tags_by_tags(tags, max_rarity=max_rarity)
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
                    text = '博士，没有找到可以锁定高星的组合'

                database.user.set_waiting(user_id, '')
                return Reply(text)

        database.user.set_waiting(user_id, '' if end else 'Recruit')

        wait = '' if end else '，请重新尝试或者发送图片试试吧\n阿米娅正在等待你发送图片...'

        return Reply('博士，没有检测到可以排列的组合%s' % wait)

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
