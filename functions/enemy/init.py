import re
import requests

from urllib import parse
from bs4 import BeautifulSoup

from message.messageType import TextImage
from modules.commonMethods import Reply


class Init:
    def __init__(self):
        self.function_id = 'checkEnemy'
        self.keyword = ['敌人', '敌方']

    @staticmethod
    def action(data):
        return Reply('博士，敌人查询功能升级中，暂时无法使用哦')

    def __action(self, data):

        message = data['text']

        for item in ['敌人(.*)', '敌方(.*)']:
            r = re.search(re.compile(item), message)
            if r:
                enemy_name = r.group(1)
                result = self.find_enemy(enemy_name)
                if result:
                    return Reply(result)
                else:
                    return Reply('博士，没有找到%s的资料呢 >.<' % enemy_name)

    @staticmethod
    def find_enemy(enemy):
        url = 'http://prts.wiki/w/%s' % (parse.quote(enemy))

        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')

        tables = soup.select('.logo-top')

        cards = []
        for level, table in enumerate(tables):
            try:
                tr = table.select('tr')

                content = []
                for item in tr:
                    sub = item.select('th') + item.select('td')
                    for sub_item in sub:
                        text = sub_item.text.strip()
                        content.append(text)

                desc = ''
                talent = ''
                attribute = {}
                skills = {}
                if content:
                    desc = content[1]

                attrs = content[2:9] + content[16:23]
                value = content[9:16] + content[23:30]
                for index, item in enumerate(attrs):
                    attribute[item.split(' ')[0]] = value[index]

                if content[30] == '天赋':
                    talent = content[31]

                if content[30] == '技能':
                    skill = True
                    start = 36
                    while skill:
                        skill_info = content[start:start + 5]
                        skills[skill_info[0]] = {
                            '初始': skill_info[1],
                            '消耗': skill_info[2],
                            '类型': skill_info[3],
                            '效果': skill_info[4]
                        }
                        start += 5
                        if content[start].split(' ')[0] == '天赋':
                            talent = content[start + 1]
                            skill = False

                indent = '　' * 2
                text = '博士，为您找到了敌方的档案资料：\n\n【%s - 等级%s】\n\n' % (enemy, level)
                text += '%s\n' % desc
                text += '%s\n' % talent
                text += '\n属性：\n'
                for name in attribute:
                    text += '%s%s：%s\n' % (indent, name, attribute[name])
                text += '\n技能：\n'
                for name in skills:
                    sub_text = '%s【%s】\n' % (indent, name)
                    for attr in skills[name]:
                        sub_text += '%s%s：%s\n' % (indent * 2, attr, skills[name][attr])
                    text += sub_text

                text += '\n档案资料鸣谢：PRTS - 玩家自由构筑的明日方舟中文Wiki'

                cards.append(TextImage(text))

            except Exception as e:
                print('Enemy', e)

        return cards
