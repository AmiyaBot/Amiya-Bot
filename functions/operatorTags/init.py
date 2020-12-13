import jieba

from jieba import posseg
from itertools import combinations
from modules.commonMethods import Reply, all_item_in_text, insert_empty
from database.baseController import BaseController

database = BaseController()
jieba.load_userdict('resource/tags.txt')


class Init:
    def __init__(self):
        self.function_id = 'operatorTags'
        self.keyword = ['公招']
        self.tags = []
        with open('resource/tags.txt') as tags:
            for item in tags.read().split('\n'):
                self.tags.append(item.split(' ')[0].strip())

    def action(self, data):
        msg_words = posseg.lcut(data['text'].replace('公招', ''))

        tags = []
        max_rarity = 5
        for item in msg_words:
            if item.word in self.tags:
                if item.word in ['资深', '资深干员']:
                    tags.append('资深干员')
                    continue
                if item.word in ['高资', '高级资深', '高级资深干员']:
                    tags.append('高级资深干员')
                    max_rarity = 6
                    continue
                tags.append(item.word)

        if tags:
            result = database.operator.find_operator_tags_by_tags(tags, max_rarity=max_rarity)
            if result:
                text = ''
                for comb in self.find_combinations(tags):
                    lst = []
                    for item in result:
                        if all_item_in_text(item[3], comb):
                            if item[2] >= 4:
                                lst.append(item)
                            else:
                                break
                    else:
                        if lst:
                            text += '\n[%s]\n' % '，'.join(comb)
                            for item in lst:
                                star = '☆' if item[2] < 5 else '★'
                                text += '[%s] %s\n' % (insert_empty(star * item[2], 5, True), item[1])

                if text:
                    text = '博士，根据标签已找到以下可以锁定高星干员的组合\n' + text
                else:
                    text = '博士，没有找到可以锁定高星的组合'

                return Reply(text)

    @staticmethod
    def find_combinations(_list):
        result = []
        for i in range(len(_list)):
            for n in combinations(_list, i):
                if n:
                    result.append(list(n))
        return result
