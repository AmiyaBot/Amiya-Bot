import os

from database.baseController import BaseController
from message.messageType import TextImage

database = BaseController()
material_images_source = 'resource/images/materials/'
skill_images_source = 'resource/images/skills/'


class MaterialCosts:
    def __init__(self, extra):
        self.keywords = []
        self.operator_list = []
        self.skill_list = []
        self.level_list = {
            '精1': -1, '精英1': -1,
            '精2': -2, '精英2': -2,
            '1级': 1, '等级1': 1,
            '2级': 2, '等级2': 2,
            '3级': 3, '等级3': 3,
            '4级': 4, '等级4': 4,
            '5级': 5, '等级5': 5,
            '6级': 6, '等级6': 6,
            '7级': 7, '等级7': 7,
            '专1': 8, '专精1': 8,
            '专2': 9, '专精2': 9,
            '专3': 10, '专精3': 10
        }
        self.skill_index_list = {
            '1技能': 1, '2技能': 2, '3技能': 3
        }
        keywords = [] + extra

        for key in self.level_list:
            keywords.append('%s 100 n' % key)
            self.keywords.append(key)
        for key in self.skill_index_list:
            keywords.append('%s 100 n' % key)
            self.keywords.append(key)

        operators = database.operator.get_all_operator()
        for item in operators:
            name = item['operator_name']
            keywords.append('%s 100 n' % name)
            self.operator_list.append(name)
            self.keywords.append(name)

        skills = database.operator.get_all_operator_skill()
        for item in skills:
            name = item['skill_name']
            self.skill_list.append(name)
            self.keywords.append(name)

        with open('resource/operators.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(keywords))

    @staticmethod
    def find_repeat_skill_name(name, skill, skill_index):
        text = ''
        if skill and skill_index == 0:
            skill_info = database.operator.get_operator_skill_by_name(skill)
            if len(skill_info):
                if name == '' and len(skill_info) > 1:
                    text += '博士，目前存在 %d 个干员拥有【%s】这个技能哦，请用比如「干员一技能专三」这种方式和阿米娅描述吧' % (len(skill_info), skill)
                item = skill_info[0]
                if name == '':
                    name = item['operator_name']
                    skill_index = item['skill_index']
                else:
                    if name == item['operator_name']:
                        skill_index = item['skill_index']

        return text, name, skill_index

    @staticmethod
    def check_evolve_costs(name, level):
        evolve = {1: '一', 2: '二'}

        result = database.operator.find_operator_evolve_costs(name, level)

        text = ''
        if len(result):
            text += '博士，这是干员%s精英%s需要的材料清单\n\n' % (name, evolve[level])
            images = []
            material_name = []
            for item in result:
                if item['material_name'] not in material_name:
                    text += '%s%s X %s\n\n' % (' ' * 12, item['material_name'], item['use_number'])
                    images.append(material_images_source + item['material_icon'] + '.png')
                    material_name.append(item['material_name'])

            icons = []
            for index, item in enumerate(images):
                if os.path.exists(item):
                    icons.append({
                        'path': item,
                        'size': (35, 35),
                        'pos': (5, 26 + index * 34)
                    })

            text = TextImage(text, icons)
        else:
            text += '博士，暂时没有找到相关的档案哦~'

        return text

    def check_mastery_costs(self, name, skill, level, skill_index=0):
        mastery = {1: '一', 2: '二', 3: '三'}

        text, name, skill_index = self.find_repeat_skill_name(name, skill, skill_index)

        if text:
            return text

        result = database.operator.find_operator_skill_mastery_costs(name, level, skill_index)

        if len(result):
            text += '博士，这是干员%s技能专精%s需要的材料清单\n\n' % (name, mastery[level])
            skills = {}
            skill_images = []
            material_images = []
            icons = []

            for item in result:
                skill_name = item['skill_name']
                if skill_name not in skills:
                    skills[skill_name] = []
                    skill_images.append(skill_images_source + item['skill_icon'] + '.png')
                skills[skill_name].append(item)
            for name in skills:
                text += '%s%s\n\n' % (' ' * 15, name)
                for item in skills[name]:
                    text += '————%s%s X %s\n\n' % (' ' * 15, item['material_name'], item['use_number'])
                    material_images.append(material_images_source + item['material_icon'] + '.png')

            for index, item in enumerate(skill_images):
                if os.path.exists(item):
                    icons.append({
                        'path': item,
                        'size': (35, 35),
                        'pos': (10, 28 + 136 * index)
                    })

            i, n = 0, 34
            for index, item in enumerate(material_images):
                if index and index % 3 == 0:
                    i += n
                if os.path.exists(item):
                    icons.append({
                        'path': item,
                        'size': (35, 35),
                        'pos': (73, 60 + i)
                    })
                i += n

            text = TextImage(text, icons)
        else:
            text += '博士，没有找到干员%s技能专精%s需要的材料清单' % (name, mastery[level])

        return text
