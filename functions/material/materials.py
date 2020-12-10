import json

from database.baseController import BaseController

database = BaseController()


class Material:
    def __init__(self):
        self.keywords = []
        self.material_list = []

        materials = database.material.get_all_material()
        for item in materials:
            self.keywords.append('%s 3 n' % item[1])
            self.material_list.append(item[1])

        with open('resource/materials.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(self.keywords))

    @staticmethod
    def check_material(name):

        rate = {
            1: '罕见',
            2: '小概率',
            3: '中概率',
            4: '大概率',
            5: '固定'
        }

        source = database.material.find_material_source(name)
        made = database.material.find_material_made(name)

        text = ''
        if source or made:
            text += '博士，材料%s可以' % name
            if source:
                text += '在以下地点通关获得...'
                for item in source:
                    if item[3] == 0:
                        text += '\n周%s 【物资筹备】' % item[2]
                    else:
                        text += '\n%s 【%s】' % (item[2], rate[int(item[3])])
                text += '\n\n' if made else ''
            if made:
                text += '通过以下配方合成...'
                for item in made:
                    text += '\n%s X %d' % (item[0], item[1])
        else:
            text += '博士，没有找到相关的档案哦~'

        return text
