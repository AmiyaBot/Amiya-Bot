import os

from core.util.common import integer
from core.util.imageCreator import TextParser, line_height, side_padding
from dataSource import DataSource, Operator
from dataSource.builder import parse_template, attr_lower_dict

from .initData import InfoInterface

material_images_source = 'resource/images/materials/'

icon_size = 36


class OperatorModules:
    def __init__(self, data: DataSource):
        self.data = data

    def find_operator_module(self, info: InfoInterface):
        operator: Operator = self.data.operators[info.name]
        modules = operator.modules()

        if modules:
            return self.build_module_content(info.name, modules)
        else:
            return f'博士，干员{info.name}尚未拥有模组哦~'

    def build_module_content(self, name, modules):
        text = f'博士，为您找到干员{name}的模组信息'
        icons = []

        i, n = 0, line_height * 2

        materials = self.data.materials
        material_images = []

        for item in modules:
            text += '\n\n【%s】\n\n' % (item['uniEquipName'])

            text += f'[解锁条件] ' \
                    f'精英{item["unlockEvolvePhase"]} - ' \
                    f'等级{item["unlockLevel"]} - ' \
                    f'信赖{int(item["unlockFavorPoint"] / 100)}%\n'

            text += '[基础属性增加]'
            if item['detail']:
                text += '\n'
                attrs = item['detail']['phases'][-1]['attributeBlackboard']
                for attr in attrs:
                    if attr['key'] in attr_lower_dict:
                        text += ' -- %s：%s\n' % (attr_lower_dict[attr['key']], integer(attr['value']))
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
                i = TextParser(text).line * line_height + side_padding + int((line_height * 3 - icon_size) / 2)
                for cost in item['itemCost']:
                    material = materials[cost['id']]
                    text += ' -- %s%s * %s\n\n' % (' ' * 15, material['material_name'], cost['count'])
                    material_images.append(material_images_source + material['material_icon'] + '.png')
                text += '\n'
            else:
                text += '无\n'

            text += '[模组故事]\n'
            text += item['uniEquipDesc']

        for index, item in enumerate(material_images):
            if index and index % 3 == 0:
                i += n
            if os.path.exists(item):
                icons.append({
                    'path': item,
                    'size': (icon_size, icon_size),
                    'pos': (30, i)
                })
            i += n

        return text, icons
