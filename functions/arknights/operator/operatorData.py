import os

from core.resource.arknightsGameData import ArknightsGameData
from core.resource.arknightsGameData.operatorBuilder import ArknightsConfig, parse_template
from core.builtin.imageCreator import TextParser
from core.builtin.messageChain import MAX_SEAT
from core.util import integer, any_match

from .initData import OperatorSearchInfo, InitData
from .operatorInfo import OperatorInfo

material_images_source = 'resource/gamedata/item/'
avatars_images_source = 'resource/gamedata/avatar/'
skill_images_source = 'resource/gamedata/skill/'

side_padding = 10
line_height = 16
icon_size = 34


class OperatorData:
    @classmethod
    def check_evolve_costs(cls, info: OperatorSearchInfo):
        operators = ArknightsGameData().operators

        if not info.name or info.name not in operators:
            return '博士，请仔细描述想要查询的信息哦'

        operator = operators[info.name]
        evolve_costs = operator.evolve_costs()

        result = []
        for item in evolve_costs:
            if item['evolve_level'] == info.level:
                material = ArknightsGameData().materials[item['use_material_id']]
                result.append({
                    'material_name': material['material_name'],
                    'material_icon': material['material_icon'],
                    'use_number': item['use_number']
                })

        return cls.__build_evolve_costs(result, info.name, info.level)

    @classmethod
    def check_mastery_costs(cls, info: OperatorSearchInfo):

        check_res = cls.check_skill_list(
            OperatorInfo.skill_operator,
            info
        )

        if type(check_res) is str:
            return check_res
        else:
            skill_list, skills_cost, skills_desc = check_res

        result = []

        for skl in skill_list:
            for item in skills_cost[skl['skill_no']]:
                if item['mastery_level'] == info.level:
                    material = ArknightsGameData().materials[item['use_material_id']]
                    result.append(
                        {
                            'skill_name': skl['skill_name'],
                            'skill_icon': skl['skill_icon'],
                            'material_name': material['material_name'],
                            'material_icon': material['material_icon'],
                            'use_number': item['use_number']
                        }
                    )

        return cls.__build_mastery_costs(result, info.name, info.level)

    @classmethod
    def find_operator_module(cls, info: OperatorSearchInfo, story: bool):
        operators = ArknightsGameData().operators

        if not info.name or info.name not in operators:
            return '博士，请仔细描述想要查询的信息哦'

        operator = operators[info.name]
        modules = operator.modules()

        if modules:
            if story:
                return cls.build_module_story(info.name, modules)
            return cls.build_module_content(info.name, modules)
        else:
            return f'博士，干员{info.name}尚未拥有模组哦~'

    @classmethod
    def get_detail_info(cls, info: OperatorSearchInfo):
        operators = ArknightsGameData().operators

        if not info.name or info.name not in operators:
            return '博士，请仔细描述想要查询的信息哦'

        operator = operators[info.name]

        detail, trust = operator.detail()
        talents = operator.talents()
        potential = operator.potential()
        building_skills = operator.building_skills()

        text = '博士，为您找到以下干员资料\n\n\n\n\n\n\n'
        icons = [
            {
                'path': avatars_images_source + operator.id + '.png',
                'size': 80,
                'pos': (side_padding, 30)
            }
        ]

        text += '%s [%s]\n%s\n\n' % (operator.name,
                                     operator.en_name,
                                     '★' * operator.rarity)

        text += '%s\n' % operator.range

        text += '【职业】%s - %s\n　%s\n\n' % (operator.classes, operator.classes_sub, detail['operator_trait'])

        text += '【生日】%s\n\n' % operator.birthday

        text += '%s\n -- 「%s」\n\n' % (detail['operator_usage'], detail['operator_quote'])

        text += '【信物】\n　%s\n\n' % detail['operator_token'] if detail['operator_token'] else ''

        text += '【精英 %s 级属性】\n' % detail['max_level']

        for key, name in ArknightsConfig.attr_dict.items():
            text += f' -- {name}：'
            if key in detail:
                text += str(integer(detail[key]))
            if key in trust and int(trust[key]):
                text += '(%s)' % integer(trust[key])
            text += '\n'

        talents_text = ''
        for item in talents:
            talents_text += '<[cl %s@#174CC6 cle]>\n　%s\n' % (item['talents_name'], item['talents_desc'])
        text += ('\n【天赋】\n%s\n' % talents_text) if talents_text else ''

        potential_text = ''
        for item in potential:
            potential_text += '　[%s] %s\n' % (InitData.potential_rank[item['potential_rank']], item['potential_desc'])
        text += ('【潜能】\n%s\n' % potential_text) if potential_text else ''

        building_text = ''
        for item in building_skills:
            building_text += '<[cl %s@#174CC6 cle]>\n　[cl 精英%s解锁@#D60008 cle]\n　%s\n' % \
                             (item['bs_name'], item['bs_unlocked'], item['bs_desc'])
        text += ('【基建技能】\n%s\n' % building_text) if building_text else ''

        info.level = 7
        info.skill = ''
        info.skill_index = 0
        skill_list, skills_cost, skills_desc = cls.check_skill_list(
            OperatorInfo.skill_operator,
            info
        )

        result = []

        for skl in skill_list:
            details = skills_desc[skl['skill_no']]
            dt = {
                'skill_name': skl['skill_name'],
                'skill_index': skl['skill_index'],
                'skill_icon': skl['skill_icon']
            }
            dt.update(details[info.level - 1])
            result.append(dt)

        if result:
            text += '【7级技能】\n\n'
            top = TextParser(text, MAX_SEAT).line * line_height + int(line_height / 2) + side_padding

            content, skill_icons = cls.build_skill_content(result, top)

            text += content
            icons += skill_icons

        return text, icons

    @classmethod
    def get_skill_data(cls, info: OperatorSearchInfo):

        check_res = cls.check_skill_list(
            OperatorInfo.skill_operator,
            info
        )

        if type(check_res) is str:
            return check_res
        else:
            skill_list, skills_cost, skills_desc = check_res

        result = []

        for skl in skill_list:
            details = skills_desc[skl['skill_no']]

            if info.level > len(details):
                return f'博士，干员{info.name}的技能等级最大只能到{len(details)}级哦'

            dt = {
                'skill_name': skl['skill_name'],
                'skill_index': skl['skill_index'],
                'skill_icon': skl['skill_icon']
            }
            dt.update(details[info.level - 1])
            result.append(dt)

        if len(result):
            text = f'博士，这是干员{info.name}技能{InitData.skill_level[info.level]}的数据\n\n'

            top = side_padding + line_height + int((line_height * 3 - icon_size) / 2)
            content, icons = cls.build_skill_content(result, top)

            text += content
            return text, icons
        else:
            return f'博士，没有找到干员{info.name}技能{InitData.skill_level[info.level]}的数据'

    @staticmethod
    def build_skill_content(result, position):
        text = ''
        skills = {}
        skill_images = []
        icons = []

        y = position
        yl = []

        for item in result:
            skill_name = item['skill_name']
            if skill_name not in skills:
                skills[skill_name] = []
                skill_images.append(skill_images_source + item['skill_icon'] + '.png')
            skills[skill_name].append(item)

        for name in skills:
            text += '%s%s\n\n' % (' ' * 15, name)
            content = ''
            index = list(skills.keys()).index(name)

            y += 48 if index else 0
            yl.append(y)

            for item in skills[name]:
                content += '%s\n' % item['range']
                content += '%s / %s' % (InitData.sp_type[item['sp_type']], InitData.skill_type[item['skill_type']])
                content += '%sSP：%s / %s\n' % (' ' * 5, item['sp_init'], item['sp_cost'])
                if item['duration'] > 0:
                    content += '持续时间：%ss\n' % item['duration']
                content += '%s\n\n' % item['description'].replace('\\\\n', '\n')
                text += content

                y += TextParser(content, MAX_SEAT).line * line_height

        for index, item in enumerate(skill_images):
            if os.path.exists(item):
                icons.append({
                    'path': item,
                    'size': icon_size,
                    'pos': (side_padding, yl[index])
                })

        return text, icons

    @staticmethod
    def check_skill_list(skill_operator, info: OperatorSearchInfo):
        operators = ArknightsGameData().operators

        if (not info.skill and not info.name) or info.name not in operators:
            return '博士，请仔细描述想要查询的信息哦'

        if info.skill and any_match(info.skill, ['α', 'β', 'γ']):
            return f'博士，"{info.skill}"这类属于泛用技能名\n请用「干员一技能专三」这种方式向阿米娅描述吧'

        if not info.name or info.name not in operators:
            if info.skill in skill_operator:
                info.name = skill_operator[info.skill]
            else:
                return '博士，无法匹配到拥有这个技能的干员哦'

        operator = operators[info.name]

        skills, skills_id, skills_cost, skills_desc = operator.skills()

        skill_index = info.skill_index
        if info.skill and not info.skill_index:
            for index, item in enumerate(skills):
                if item['skill_name'] == info.skill:
                    skill_index = index + 1
                    break

        if skill_index > len(skills_id):
            return f'博士，干员{info.name}的只有{len(skills_id)}个技能哦'

        skill_list = [skills[skill_index - 1]] if skill_index else skills

        return skill_list, skills_cost, skills_desc

    @staticmethod
    def build_module_content(name, modules):
        text = f'博士，为您找到干员{name}的模组信息'
        icons = []

        i, n = 0, line_height * 2

        materials = ArknightsGameData().materials
        material_images = []

        for item in modules:
            text += '\n\n【%s】\n\n' % item['uniEquipName']

            text += f'[解锁条件] ' \
                    f'精英{item["unlockEvolvePhase"]} - ' \
                    f'等级{item["unlockLevel"]} - ' \
                    f'信赖{int(item["unlockFavorPoint"] / 100)}%\n'

            text += '[基础属性增加]'
            if item['detail']:
                text += '\n'
                attrs = item['detail']['phases'][-1]['attributeBlackboard']
                for attr in attrs:
                    if attr['key'] in ArknightsConfig.attr_lower_dict:
                        text += ' -- %s：%s\n' % (ArknightsConfig.attr_lower_dict[attr['key']], integer(attr['value']))
                text += '\n'
            else:
                text += '无\n'

            text += '[分支特性更新]'
            if item['detail']:
                text += '\n'
                detail = item['detail']['phases'][-1]['parts']
                for part in detail:
                    if part['overrideTraitDataBundle']['candidates'] is None:
                        continue
                    for candidate in part['overrideTraitDataBundle']['candidates']:
                        blackboard = candidate['blackboard']
                        if candidate['additionalDescription']:
                            text += ' -- 新增：%s\n' % parse_template(blackboard, candidate['additionalDescription'])
                        if candidate['overrideDescripton']:
                            text += ' -- 覆盖：%s\n' % parse_template(blackboard, candidate['overrideDescripton'])
                text += '\n'
            else:
                text += '无\n'

            text += '[解锁任务]'
            if item['missions']:
                text += '\n'
                for mission in item['missions']:
                    text += ' -- 任务%s：%s\n' % (mission['uniEquipMissionSort'], mission['desc'])
                text += '\n'
            else:
                text += '无\n'

            text += '[解锁材料]'
            if item['itemCost']:
                text += '\n\n'
                i = TextParser(text, MAX_SEAT).line * line_height + side_padding + int(
                    (line_height * 3 - icon_size) / 2)
                for cost in item['itemCost']:
                    material = materials[cost['id']]
                    text += ' -- %s%s * %s\n\n' % (' ' * 15, material['material_name'], cost['count'])
                    material_images.append(material_images_source + material['material_icon'] + '.png')
                text += '\n'
            else:
                text += '无\n'

        for index, item in enumerate(material_images):
            if index and index % 3 == 0:
                i += n
            if os.path.exists(item):
                icons.append({
                    'path': item,
                    'size': icon_size,
                    'pos': (30, i)
                })
            i += n

        return text, icons

    @staticmethod
    def build_module_story(name, modules):
        text = f'博士，为您找到干员{name}的模组故事'
        icons = []

        for item in modules:
            text += '\n\n【%s】\n\n' % item['uniEquipName']
            text += item['uniEquipDesc']

        return text, icons

    @staticmethod
    def __build_evolve_costs(result, name, level):
        evolve = {1: '一', 2: '二'}
        icons = []

        if len(result):
            text = '博士，这是干员%s精英%s需要的材料清单\n\n' % (name, evolve[level])
            images = []
            material_name = []
            for item in result:
                if item['material_name'] not in material_name:
                    text += '%s%s * %s\n\n' % (' ' * 12, item['material_name'], item['use_number'])
                    images.append(material_images_source + item['material_icon'] + '.png')
                    material_name.append(item['material_name'])

            for index, item in enumerate(images):
                if os.path.exists(item):
                    icons.append({
                        'path': item,
                        'size': icon_size,
                        'pos': (5, 26 + index * 34)
                    })
        else:
            text = '博士，暂时没有找到相关的档案哦~'

        return text, icons

    @staticmethod
    def __build_mastery_costs(result, name, level):
        mastery = {1: '一', 2: '二', 3: '三'}
        icons = []

        if len(result):
            text = f'博士，这是干员{name}技能专精{mastery[level]}需要的材料清单\n'
            skills = {}
            skill_images = []
            material_images = []

            for item in result:
                skill_name = item['skill_name']
                if skill_name not in skills:
                    skills[skill_name] = []
                    skill_images.append(skill_images_source + item['skill_icon'] + '.png')
                skills[skill_name].append(item)

            for name in skills:
                text += '\n%s%s\n\n\n' % (' ' * 15, name)
                for item in skills[name]:
                    text += ' -- %s%s * %s\n\n' % (' ' * 15, item['material_name'], item['use_number'])
                    material_images.append(material_images_source + item['material_icon'] + '.png')

            top = side_padding + line_height + int((line_height * 3 - icon_size) / 2)
            content_height = line_height * 10
            for index, item in enumerate(skill_images):
                if os.path.exists(item):
                    icons.append({
                        'path': item,
                        'size': icon_size,
                        'pos': (side_padding, top + content_height * index)
                    })

            top += line_height * 3
            i, n = 0, line_height * 2
            for index, item in enumerate(material_images):
                if index and index % 3 == 0:
                    i += n * 2
                if os.path.exists(item):
                    icons.append({
                        'path': item,
                        'size': icon_size,
                        'pos': (30, top + i)
                    })
                i += n
        else:
            text = f'博士，没有找到干员{name}技能专精{mastery[level]}需要的材料清单'

        return text, icons
