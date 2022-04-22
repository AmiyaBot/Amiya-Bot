import os

from core.resource.arknightsGameData import ArknightsGameData, ArknightsGameDataResource
from core.resource.arknightsGameData.operatorBuilder import ArknightsConfig, parse_template
from core.builtin.imageCreator import TextParser
from core.builtin.messageChain import MAX_SEAT
from core.util import integer, any_match, snake_case_to_pascal_case

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
    async def get_detail_info(cls, info: OperatorSearchInfo):
        operators = ArknightsGameData().operators

        if not info.name or info.name not in operators:
            return None

        operator = operators[info.name]

        detail, trust = operator.detail()
        modules = operator.modules()

        module_attr = {}
        if modules:
            module = modules[-1]
            if module['detail']:
                attrs = module['detail']['phases'][-1]['attributeBlackboard']
                for attr in attrs:
                    module_attr[snake_case_to_pascal_case(attr['key'])] = integer(attr['value'])

        info.level = 7
        info.skill = ''
        info.skill_index = 0
        skill_list, skills_cost, skills_desc = cls.check_skill_list(
            OperatorInfo.skill_operator,
            info
        )
        return {
            'info': {
                'id': operator.id,
                'name': operator.name,
                'en_name': operator.en_name,
                'rarity': operator.rarity,
                'range': operator.range,
                'classes': operator.classes,
                'classes_sub': operator.classes_sub,
                'birthday': operator.birthday
            },
            'skin': await ArknightsGameDataResource.get_skin_file(operator, operator.skins()[0]),
            'trust': trust,
            'detail': detail,
            'modules': module_attr,
            'talents': operator.talents(),
            'potential': operator.potential(),
            'building_skills': operator.building_skills(),
            'skill_list': skill_list,
            'skills_cost': skills_cost,
            'skills_desc': skills_desc,
        }

    @classmethod
    async def get_level_up_cost(cls, info: OperatorSearchInfo):
        operators = ArknightsGameData().operators
        materials = ArknightsGameData().materials

        if not info.name or info.name not in operators:
            return None

        operator = operators[info.name]
        evolve_costs = operator.evolve_costs()

        evolve_costs_list = {}
        for item in evolve_costs:
            material = materials[item['use_material_id']]

            if item['evolve_level'] not in evolve_costs_list:
                evolve_costs_list[item['evolve_level']] = []

            evolve_costs_list[item['evolve_level']].append({
                'material_name': material['material_name'],
                'material_icon': material['material_icon'],
                'use_number': item['use_number']
            })

        skills, skills_id, skills_cost, skills_desc = operator.skills()

        skills_cost_list = {}
        for item in skills_cost:
            material = materials[item['use_material_id']]
            skill_no = item['skill_no'] or 'common'

            if skill_no and skill_no not in skills_cost_list:
                skills_cost_list[skill_no] = {}

            if item['level'] not in skills_cost_list[skill_no]:
                skills_cost_list[skill_no][item['level']] = []

            skills_cost_list[skill_no][item['level']].append({
                'material_name': material['material_name'],
                'material_icon': material['material_icon'],
                'use_number': item['use_number']
            })

        skins = operator.skins()
        skin = skins[1] if len(skins) > 1 else skins[0]

        return {
            'skin': await ArknightsGameDataResource.get_skin_file(operator, skin),
            'evolve_costs': evolve_costs_list,
            'skills': skills,
            'skills_cost': skills_cost_list
        }

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
