import os

from core.util import log
from core.util.imageCreator import line_height, side_padding
from dataSource import DataSource

PL = {
    'SOMETIMES': '罕见',
    'OFTEN': '小概率',
    'USUAL': '中概率',
    'ALMOST': '大概率',
    'ALWAYS': '固定'
}
TY = {
    'WORKSHOP': ('加工站', '合成'),
    'MANUFACTURE': ('制造站', '生产')
}
material_images_source = 'resource/images/materials/'

icon_size = 36


class MaterialData:
    def __init__(self, data: DataSource):
        self.data = data
        self.material_list = []

        self.init_material()

    def init_material(self):
        log.info('building material\'s names keywords dict...')

        materials = self.data.materials_map
        keywords = []

        for name in materials.keys():
            self.material_list.append(name)
            keywords.append('%s 500 n' % name)

        with open('resource/materials.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(keywords))

    def check_material(self, name):

        if name not in self.data.materials_map:
            return False

        material = self.data.materials[self.data.materials_map[name]]
        material_id = material['material_id']
        material_images = []

        text = f'博士，为你找到材料【{name}】的档案\n\n\n\n\n\n\n'
        icons = [
            {
                'path': material_images_source + material['material_icon'] + '.png',
                'size': (80, 80),
                'pos': (side_padding, side_padding + line_height + int((line_height * 6 - 80) / 2))
            }
        ]

        if material_id in self.data.materials_made:
            made = self.data.materials_made[material_id]

            text += '可在【%s】通过以下配方%s：\n\n' % TY[made[0]['made_type']]
            for item in made:
                item_material = self.data.materials[item['use_material_id']]

                text += '%s%s * %s\n\n' % (' ' * 15, item_material['material_name'], item['use_number'])
                material_images.append(material_images_source + item_material['material_icon'] + '.png')

        if material_id in self.data.materials_source:
            source = self.data.materials_source[material_id]

            s_main = {
                'place': '主线关卡',
                'map': []
            }
            s_act = {
                'place': '活动',
                'map': []
            }

            for code in source.keys():
                if 'main' in code:
                    s_main['map'].append(code)
                else:
                    s_act['map'].append(code)

            for item in [s_main, s_act]:
                if item['map']:
                    text += '\n\n可在以下【%s】地图掉落：\n\n' % item['place']
                    for code in sorted(item['map']):
                        item = source[code]
                        stage = self.data.stages[code]
                        text += '【%s】%s %s\n' % (stage['stage_name'], stage['stage_code'], PL[item['source_rate']])

        for index, item in enumerate(material_images):
            if os.path.exists(item):
                icons.append({
                    'path': item,
                    'size': (icon_size, icon_size),
                    'pos': (side_padding, line_height * 9 + index * line_height * 2)
                })

        text += '\n' + material['material_desc']

        return text, icons
