import jieba

from jieba import posseg
from itertools import combinations
from modules.commonMethods import Reply, all_item_in_text, insert_empty
from database.baseController import BaseController

database = BaseController()
jieba.load_userdict('resource/tags.txt')


class Init:
    def __init__(self):
        self.function_id = 'recruit'
        self.keyword = ['公招']
        self.tags = []
        with open('resource/tags.txt', encoding='utf-8') as tags:
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
                    if item[1] not in operators:
                        operators[item[1]] = list(item)
                    else:
                        operators[item[1]][3] += item[3]

                text = ''
                for comb in [tags] if len(tags) == 1 else self.find_combinations(tags):
                    lst = []
                    for name in operators:
                        item = operators[name]
                        if all_item_in_text(item[3], comb):
                            if item[2] == 6 and '高级资深干员' not in comb:
                                continue
                            if item[2] >= 4 or item[2] == 1:
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
                                star = '☆' if item[2] < 5 else '★'
                                text += '[%s] %s\n' % (insert_empty(star * item[2], 6, True), item[1])

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
