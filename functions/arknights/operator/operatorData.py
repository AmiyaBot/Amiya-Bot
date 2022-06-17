import os
import copy

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
        materials = ArknightsGameData().materials

        if not info.name or info.name not in operators:
            return '博士，请仔细描述想要查询的信息哦'

        operator = operators[info.name]
        modules = copy.deepcopy(operator.modules())

        if story:
            return cls.find_operator_module_story(info.name, modules)

        def parse_trait_data(data):
            if data is None:
                return
            for candidate in data:
                blackboard = candidate['blackboard']
                if candidate['additionalDescription']:
                    candidate['additionalDescription'] = parse_template(blackboard,
                                                                        candidate['additionalDescription'])
                if candidate['overrideDescripton']:
                    candidate['overrideDescripton'] = parse_template(blackboard,
                                                                     candidate['overrideDescripton'])

        def parse_talent_data(data):
            if data is None:
                return
            for candidate in data:
                blackboard = candidate['blackboard']
                if candidate['upgradeDescription']:
                    candidate['upgradeDescription'] = parse_template(blackboard,
                                                                     candidate['upgradeDescription'])

        for item in modules:
            if item['itemCost']:
                for lvl, item_cost in item['itemCost'].items():
                    for i, cost in enumerate(item_cost):
                        material = materials[cost['id']]
                        item_cost[i] = {
                            **cost,
                            'info': material
                        }

            if item['detail']:
                for stage in item['detail']['phases']:
                    for part in stage['parts']:
                        parse_trait_data(part['overrideTraitDataBundle']['candidates'])
                        parse_talent_data(part['addOrOverrideTalentDataBundle']['candidates'])

        return modules

    @staticmethod
    def find_operator_module_story(name, modules):
        text = f'博士，为您找到干员{name}的模组故事'

        for item in modules:
            text += '\n\n【%s】\n\n' % item['uniEquipName']
            text += item['uniEquipDesc']

        return text
