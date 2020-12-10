import json

from database.baseController import BaseController

database = BaseController()


class MaterialCosts:
    def __init__(self, extra):
        self.keywords = []
        self.operator_list = []
        self.skill_list = []
        self.level_list = {
            '精一': 1, '精1': 1, '精英一': 1, '精英1': 1,
            '精二': 2, '精2': 2, '精英二': 2, '精英2': 2,
            '专一': 3, '专1': 3, '专精一': 3, '专精1': 3,
            '专二': 4, '专2': 4, '专精二': 4, '专精2': 4,
            '专三': 5, '专3': 5, '专精三': 5, '专精3': 5
        }
        self.skill_index_list = {
            '一技能': 1, '二技能': 2, '三技能': 3,
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
            keywords.append('%s 100 n' % item[1])
            self.operator_list.append(item[1])
            self.keywords.append(item[1])

        skills = database.operator.get_all_operator_skill()
        for item in skills:
            self.skill_list.append(item[3])
            self.keywords.append(item[3])

        with open('resource/operators.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(keywords))

    @staticmethod
    def check_evolve_costs(name, level):
        evolve = {1: '一', 2: '二'}

        result = database.operator.find_operator_evolve_costs(name, level)

        text = ''
        if len(result):
            text += '博士，找到啦！是干员%s精英%s需要的材料清单\n\n' % (name, evolve[level])
            for item in result:
                text += '%s X %s\n' % (item[0], item[1])
        else:
            text += '博士，没有找到相关的档案哦~'

        return text

    @staticmethod
    def check_mastery_costs(name, skill, level, skill_index=0):
        mastery = {1: '一', 2: '二', 3: '三'}

        text = ''

        if skill and skill_index == 0:
            skill_info = database.operator.get_operator_skill_by_name(skill)
            if len(skill_info) > 1:
                if name == '':
                    text += '博士，目前有%d个干员拥有%s这个技能哦，请选出其中一位和阿米娅说吧' % (len(skill_info), skill)
                    return text
                for item in skill_info:
                    if item[4] == name:
                        skill_index = item[2]
                if skill_index == 0:
                    text += '博士，干员%s没有%s这个技能哦' % (name, skill)
                    return text
            else:
                skill_index = skill_info[0][2]
                if name == '':
                    name = skill_info[0][4]
                else:
                    if name != skill_info[0][4]:
                        text += '博士，干员%s没有%s这个技能哦' % (name, skill)
                        return text

        result = database.operator.find_operator_skill_mastery_costs(name, level, skill_index)

        if len(result):
            text += '博士，找到啦！是干员%s技能专精%s需要的材料清单\n\n' % (name, mastery[level])
            skills = {}
            for item in result:
                if item[0] not in skills:
                    skills[item[0]] = []
                skills[item[0]].append(item)
            for name in skills:
                text += '%s\n' % name
                for item in skills[name]:
                    text += '---- %s X %s\n' % (item[2], item[3])
        else:
            text += '博士，没有找到相关的档案哦~'

        return text
