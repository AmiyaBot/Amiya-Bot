import json
import jieba
import requests

from urllib import parse
from jieba import posseg
from bs4 import BeautifulSoup
from modules.commonMethods import Reply, word_in_sentence
from .materialsCosts import MaterialCosts

with open('resource/words/voices.json', encoding='utf-8') as voices:
    voices = json.load(voices)
    keywords = []
    for key in voices:
        keywords.append('%s 100 n' % key)

material = MaterialCosts(keywords)
jieba.load_userdict('resource/operators.txt')


class Init:
    def __init__(self):
        self.function_id = 'checkOperator'
        self.keyword = voices + material.keywords

    def action(self, data):
        msg_words = posseg.lcut(data['text'])

        name = ''
        skill = ''
        level = 0

        for item in msg_words:
            if (name == '' or name == '阿米娅') and item.word in material.operator_list:
                name = item.word
            if level == 0 and item.word in material.level_list:
                level = material.level_list[item.word]

        for item in material.skill_list:
            if item in data['text']:
                skill = item

        if name == '' and skill == '':
            return Reply('博士，想查询哪位干员或技能的资料呢？请再说一次吧')
        if level != 0:
            if level <= 2:
                result = material.check_evolve_costs(name, level)
            else:
                skill_index = 0
                for _key in material.skill_index_list:
                    if _key in data['text']:
                        skill_index = material.skill_index_list[_key]

                level -= 2
                result = material.check_mastery_costs(name, skill, level, skill_index=skill_index)

            if len(result) < 20:
                return Reply(result)

            return Reply(result)

        if word_in_sentence(data['text'], ['精英', '专精']):
            return Reply('博士，要告诉阿米娅精英或专精等级哦')

        if word_in_sentence(data['text'], ['语音']):
            for item in msg_words:
                if item.word in voices:
                    return self.find_voice(name, item.word, data['type'])

    @staticmethod
    def find_voice(operator, voice, message_type):
        url = 'http://prts.wiki/w/%s/%s' % (parse.quote(operator), parse.quote('语音记录'))

        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.select('table.nodesktop tbody')

        if len(table):
            tr = table[0].select('tr')
            for index, item in enumerate(tr):
                name = item.select('th:first-child b')
                if name and voice in name[0].string:
                    content = tr[index + 1].select('p')
                    text = content[1].get_text()
                    source = 'PRTS - 玩家自由构筑的明日方舟中文Wiki'
                    text = '博士，为您找到干员%s%s的语音档案：\n\n%s\n\n档案资料鸣谢：%s' % (operator, voice, text, source)
                    return Reply(text)
        return Reply('博士，没有找到干员%s%s相关的语音档案哦')
