import os

from core.resource.arknightsGameData import ArknightsGameData, ArknightsGameDataResource
from core.resource.arknightsGameData.operatorBuilder import ArknightsConfig, parse_template
from core.builtin.imageCreator import TextParser
from core.builtin.messageChain import MAX_SEAT
from core.util import integer, snake_case_to_pascal_case

from .initData import OperatorSearchInfo

material_images_source = 'resource/gamedata/item/'
avatars_images_source = 'resource/gamedata/avatar/'
skill_images_source = 'resource/gamedata/skill/'

side_padding = 10
line_height = 16
icon_size = 34


class OperatorData:
    @classmethod
    async def get_operator_detail(cls, info: OperatorSearchInfo):
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

        skills, skills_id, skills_cost, skills_desc = operator.skills()

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
            'skill_list': skills,
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
    async def get_skills_detail(cls, info: OperatorSearchInfo):
        operators = ArknightsGameData().operators

        if not info.name or info.name not in operators:
            return None

        operator = operators[info.name]
        skills, skills_id, skills_cost, skills_desc = operator.skills()

        return {
            'skills': skills,
            'skills_desc': skills_desc
        }

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
