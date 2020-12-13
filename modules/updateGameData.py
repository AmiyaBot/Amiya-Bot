import re
import json
import requests

from bs4 import BeautifulSoup
from database.baseController import BaseController

database = BaseController()

classes = {
    '先锋': 1, '近卫': 2, '重装': 3, '狙击': 4, '术师': 5, '辅助': 6, '医疗': 7, '特种': 8
}
unavailable = [
    # 无法正常获得
    '阿米娅', '暴行', '断罪者',
    # 红票或其他购买渠道获得
    '嘉维尔', '讯使', '微风', '伊桑', '坚雷', '清流',
    # 公招限定
    '因陀罗', '火神', '艾丝黛尔',
    # 活动限定
    '格拉尼', '锡兰', '炎客', '拜松', '雪雉', '铸铁', '苦艾', '亚叶', '特米米', '薄绿', '鞭刃',
    # 危机合约
    '柏喙', '稀音',
    # 集成战略
    '预备干员-近战', '预备干员-狙击', '预备干员-后勤', '预备干员-术师', 'Sharp', 'Stormeye', 'Pith', 'Touch'
]
limit = [
    # 限定
    '年', 'W', '迷迭香'
]


class UpdateGameData:
    def __init__(self):
        pass

    @staticmethod
    def get_json_data():
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) '
                          'AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        url = 'https://www.bigfun.cn/tools/aktools/'
        new_id = ''

        html = requests.get(url, headers=headers)
        if html.status_code == 200:
            content = html.content
            soup = BeautifulSoup(content.decode('utf-8'), 'html.parser')
            script = soup.find_all('script', type='module')[0]

            r = re.search(r'/(\d+)/', str(script))
            if r:
                new_id = r.group(1)

        if new_id == '':
            return {}

        static = 'https://www.bigfun.cn/static/aktools/%s/data' % new_id
        resource = {
            'charMaterials': '%s/charMaterials.json' % static,
            'material': '%s/material.json' % static,
            'tagsRelation': '%s/akhr.json' % static
        }

        result = {}
        for item in resource.keys():
            stream = requests.get(resource[item], headers=headers, stream=True)
            if stream.status_code == 200:
                result[item] = json.loads(stream.content)

        relation = {}
        for i in result['material']:
            relation[result['material'][i]['name']] = i
        result['materialRelation'] = relation

        return result

    @staticmethod
    def get_operators(fld=0):
        operators = database.operator.get_all_operator()
        operators_list = {}
        for item in operators:
            operators_list[item[1]] = item[fld]
        return operators_list

    @staticmethod
    def get_skills():
        skills = database.operator.get_all_operator_skill()
        skills_list = {}
        for item in skills:
            skills_list[item[3] + '-' + str(item[1])] = item[0]
        return skills_list

    @staticmethod
    def t_material(data):
        material = data['material']
        data_list = []
        for i in material:
            data_list.append({
                'id': i,
                'name': material[i]['name'],
                'nickname': ''
            })
        database.material.add_material(data_list)

    @staticmethod
    def t_material_made(data):
        material = data['material']
        data_list = []
        for i in material:
            if material[i]['madeof']:
                for name in material[i]['madeof']:
                    data_list.append({
                        'material_id': i,
                        'use_material_id': data['materialRelation'][name],
                        'use_number': material[i]['madeof'][name]
                    })
        database.material.add_material_made(data_list)

    @staticmethod
    def t_material_source(data):
        rate = {
            '': 0, '罕见': 1, '小概率': 2, '中概率': 3, '大概率': 4, '固定': 5
        }
        material = data['material']
        data_list = []
        for i in material:
            if material[i]['source']:
                for name in material[i]['source']:
                    data_list.append({
                        'material_id': i,
                        'source_place': name,
                        'source_rate': rate[material[i]['source'][name]]
                    })
        database.material.add_material_source(data_list)

    @staticmethod
    def t_operator(data):
        operator = data['charMaterials']
        data_list = []
        for name in operator:
            item = operator[name]
            if item['profession'] != '其它':
                data_list.append({
                    'operator_name': item['name'],
                    'operator_rarity': item['rarity'] + 1,
                    'operator_class': classes[item['profession']],
                    'available': 1 if item['rarity'] >= 2 and item['name'] not in unavailable else 0,
                    'in_limit': 1 if item['name'] in limit else 0
                })
        database.operator.add_operator(data_list)

    def t_operator_evolve_costs(self, data):
        operator = data['charMaterials']
        operators_list = self.get_operators()

        data_list = []
        for name in operator:
            item = operator[name]
            if item['profession'] != '其它':
                operator_id = operators_list[name]
                for index, item in enumerate(item['evolveCosts']):
                    if item:
                        for detail in item:
                            data_list.append({
                                'operator_id': operator_id,
                                'evolve_level': index,
                                'use_material_id': detail['id'],
                                'use_number': detail['count']
                            })
        database.operator.add_operator_evolve_costs(data_list)

    def t_operator_skill(self, data):
        operator = data['charMaterials']
        operators_list = self.get_operators()

        data_list = []
        for name in operator:
            item = operator[name]
            if item['profession'] != '其它':
                operator_id = operators_list[name]
                for index, item in enumerate(item['sskillCosts']):
                    data_list.append({
                        'operator_id': operator_id,
                        'skill_index': index + 1,
                        'skill_name': item['skillName']
                    })
        database.operator.add_operator_skill(data_list)

    def t_operator_skill_mastery_costs(self, data):
        operator = data['charMaterials']
        operators_list = self.get_operators()
        skills_list = self.get_skills()

        data_list = []
        for name in operator:
            operator_item = operator[name]
            if operator_item['profession'] != '其它':
                operator_id = operators_list[name]
                for skill in operator_item['sskillCosts']:
                    skill_id = skills_list[skill['skillName'] + '-' + str(operator_id)]
                    for index, cost in enumerate(skill['levelUpCost']):
                        if cost['levelUpCost']:
                            for item in cost['levelUpCost']:
                                data_list.append({
                                    'skill_id': skill_id,
                                    'mastery_level': index + 1,
                                    'use_material_id': item['id'],
                                    'use_number': item['count']
                                })
        database.operator.add_operator_skill_mastery_costs(data_list)

    def t_operator_tags_relation(self, data):
        operator = data['tagsRelation']
        operator_list = self.get_operators(3)

        wd = ' 100 a'

        cls = []
        for item in classes.keys():
            cls.append(item + wd)

        cls_rel = {value: key for (key, value) in classes.items()}

        tags = cls + [
            '资深' + wd,
            '高资' + wd,
            '高级资深' + wd,
        ]
        data_list = []
        for item in operator:
            item['tags'] += [
                cls_rel[
                    operator_list[
                        item['name']
                    ]
                ]
            ]
            data_list.append({
                'operator_name': item['name'],
                'operator_rarity': item['level'],
                'operator_tags': ','.join(item['tags'])
            })
            for tag in item['tags']:
                key = tag + wd
                if key not in tags:
                    tags.append(key)

        with open('resource/tags.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(tags))

        database.operator.add_operator_tags_relation(data_list)

    def reset_all_data(self):
        data = self.get_json_data()
        if data:
            database.material.truncate_all()
            self.t_material(data)
            self.t_material_made(data)
            self.t_material_source(data)
            self.t_operator(data)
            self.t_operator_evolve_costs(data)
            self.t_operator_skill(data)
            self.t_operator_skill_mastery_costs(data)
            self.t_operator_tags_relation(data)
