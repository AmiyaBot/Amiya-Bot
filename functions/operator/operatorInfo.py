import re

from database.baseController import BaseController
from message.messageType import TextImage
from functions.operator.materialsCosts import MaterialCosts, skill_images_source

database = BaseController()

skill_level = {
    1: '等级1',
    2: '等级2',
    3: '等级3',
    4: '等级4',
    5: '等级5',
    6: '等级6',
    7: '等级7',
    8: '专精1',
    9: '专精2',
    10: '专精3'
}
skill_type = {
    0: '被动',
    1: '手动触发',
    2: '自动触发'
}
sp_type = {
    1: '自动回复',
    2: '攻击回复',
    4: '受击回复',
    8: '被动'
}


class OperatorInfo:
    def __init__(self):
        self.stories_title = database.operator.get_all_stories_title()
        self.stories_keyword = []

        for item in self.stories_title:
            item = re.compile(r'？+', re.S).sub('', item)
            if item:
                self.stories_keyword.append(item + ' 100 n')

        with open('resource/stories.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(self.stories_keyword))

    @staticmethod
    def get_skill_data(name, skill, level, skill_index=0):

        text, name, skill_index = MaterialCosts.find_repeat_skill_name(name, skill, skill_index)

        if text:
            return text

        result = database.operator.find_operator_skill_description(name, level, skill_index)

        if len(result):
            text += '博士，这是干员%s技能%s的数据\n\n' % (name, skill_level[level])
            skills = {}
            skill_images = []

            for item in result:
                skill_name = item['skill_name']
                if skill_name not in skills:
                    skills[skill_name] = []
                    skill_images.append(skill_images_source + item['skill_icon'] + '.png')
                skills[skill_name].append(item)
            for name in skills:
                text += '【%s】\n\n' % name
                for item in skills[name]:
                    text += '%s / %s' % (sp_type[item['sp_type']], skill_type[item['skill_type']])
                    text += '%sSP：%s / %s\n' % (' ' * 5, item['sp_init'], item['sp_cost'])
                    if item['duration'] > 0:
                        text += '持续时间：%ss\n' % item['duration']
                    text += '%s\n\n' % item['description']

            return TextImage(text)
        else:
            return '博士，没有找到干员%s技能%s的数据' % (name, skill_level[level])
