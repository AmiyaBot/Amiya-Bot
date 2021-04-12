import os

from database.baseController import BaseController
from message.messageType import TextImage

database = BaseController()
material_images_source = 'resource/images/materials/'


class Material:
    def __init__(self):
        self.keywords = []
        self.material_list = []

        materials = database.material.get_all_material()
        for item in materials:
            self.keywords.append('%s 100 n' % item['material_name'])
            self.material_list.append(item['material_name'])

        with open('resource/materials.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(self.keywords))

    @staticmethod
    def check_material(name):
        pl = {
            'SOMETIMES': '罕见',
            'OFTEN': '小概率',
            'USUAL': '中概率',
            'ALMOST': '大概率',
            'ALWAYS': '固定'
        }
        ty = {
            'WORKSHOP': ('加工站', '合成'),
            'MANUFACTURE': ('制造站', '生产')
        }

        made = database.material.find_material_made(name)
        source = database.material.find_material_source(name, only_main=True)
        material = database.material.get_material(name)

        text = '博士，为你找到材料【%s】的档案\n\n\n\n\n\n\n' % name
        icons = [
            {
                'path': material_images_source + material['material_icon'] + '.png',
                'size': (80, 80),
                'pos': (10, 30)
            }
        ]

        if made or source:
            material_images = []

            if made:
                text += '可在【%s】通过以下配方%s：\n\n' % ty[made[0]['made_type']]
                for item in made:
                    text += '%s%s X %s\n\n' % (' ' * 12, item['material_name'], item['use_number'])
                    material_images.append(material_images_source + item['material_icon'] + '.png')

            if source:
                text += '可在以下非活动地图掉落：\n\n'
                source = {item['stage_code']: item for item in source}
                for code in sorted(source):
                    stage = source[code]
                    text += '【%s %s】 %s\n' % (stage['stage_code'], stage['stage_name'], pl[stage['source_rate']])

            for index, item in enumerate(material_images):
                if os.path.exists(item):
                    icons.append({
                        'path': item,
                        'size': (35, 35),
                        'pos': (5, 145 + index * 34)
                    })

        text += '\n' + material['material_desc']

        return TextImage(text, icons)
