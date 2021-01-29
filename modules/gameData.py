import os
import time
import json
import requests

from database.baseController import BaseController

database = BaseController()
classes = {
    'PIONEER': '先锋',
    'WARRIOR': '近卫',
    'TANK': '重装',
    'SNIPER': '狙击',
    'CASTER': '术师',
    'SUPPORT': '辅助',
    'MEDIC': '医疗',
    'SPECIAL': '特种'
}
types = {
    'MELEE': '近战',
    'RANGED': '远程'
}
high_star = {
    5: '资深干员',
    6: '高级资深干员'
}
unavailable = [
    # 无法正常获得
    '阿米娅', '暴行', '断罪者',
    # 红票或其他购买渠道获得
    '嘉维尔', '讯使', '微风', '伊桑', '坚雷', '清流',
    # 公招限定
    '因陀罗', '火神', '艾丝黛尔',
    # 活动限定
    '格拉尼', '锡兰', '炎客', '拜松', '雪雉', '铸铁', '苦艾', '亚叶', '特米米', '薄绿', '鞭刃', '罗宾',
    # 危机合约
    '柏喙', '稀音', '图耶',
    # 集成战略
    '预备干员-近战', '预备干员-狙击', '预备干员-后勤', '预备干员-术师', 'Sharp', 'Stormeye', 'Pith', 'Touch'
]
limit = [
    # 限定
    '年', 'W', '迷迭香'
]


class Operator:
    def __init__(self, data):
        self.id = data['No']
        self.name = data['name']
        self.en_name = data['en']
        self.rarity = data['tags'][0] + 1
        self.classes = classes[data['class']]
        self.classes_code = list(classes.keys()).index(data['class']) + 1
        self.type = types[data['tags'][1]]
        self.tags = data['tags'][2:]
        self.recruit = data['gkzm']


class OperatorTags:
    def __init__(self, name, rarity):
        self.rarity = rarity
        self.name = name
        self.tags = []

    def append(self, tag):
        self.tags.append({
            'operator_name': self.name,
            'operator_rarity': self.rarity,
            'operator_tags': tag
        })


class GameData:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) '
                          'AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
            'Referer': 'https://www.kokodayo.fun/'
        }
        self.data_source = 'https://andata.somedata.top/data-2020'
        self.pics_source = 'https://andata.somedata.top/dataX/item/pic'
        self.pics_path = 'resource/images'

    def get_key(self):
        url = 'https://api.kokodayo.fun/api/base/info'
        info = requests.get(url, headers=self.headers)
        if info.status_code == 200:
            info = info.json()
            if info['ok']:
                return info['result']['agent']['char']['key']

    def get_json_data(self, title, name):
        url = '%s/%s/%s.json' % (self.data_source, title, name)
        stream = requests.get(url, headers=self.headers, stream=True)
        if stream.status_code == 200:
            content = json.loads(stream.content)
            return content

    def get_pic(self, name, _type):
        url = '%s/%s.png' % (self.pics_source, name)
        path = '%s/%s/%s.png' % (self.pics_path, _type, name)
        if os.path.exists(path) is False:
            stream = requests.get(url, headers=self.headers, stream=True)
            if stream.status_code == 200:
                with open(path, mode='wb') as _pic:
                    _pic.write(stream.content)

    def get_operators_list(self, new_id):
        content = self.get_json_data('char/list', new_id)
        if content:
            operators = []
            for item in content:
                if item['class'] in classes:
                    operators.append(item)
            return operators

    def save_operator_data(self, data):
        operator = Operator(data)
        rarity = operator.rarity

        # todo 保存基础信息
        database.operator.add_operator([{
            'operator_no': operator.id,
            'operator_name': operator.name,
            'operator_rarity': rarity,
            'operator_class': operator.classes_code,
            'available': 1 if rarity >= 2 and operator.name not in unavailable else 0,
            'in_limit': 1 if operator.name in limit else 0
        }])
        print(' --- 基础信息保存完毕...')

        # todo 若此干员为可公招的干员，保存Tags信息
        if operator.recruit:
            operator_tags = OperatorTags(operator.name, rarity)
            operator_tags.append(operator.classes)
            operator_tags.append(operator.type)

            if rarity in high_star:
                operator_tags.append(high_star[rarity])

            for tag in operator.tags:
                operator_tags.append(tag)

            database.operator.add_operator_tags_relation(operator_tags.tags)
            print(' --- 公招信息保存完毕...')

        # todo 保存干员的详细信息
        self.save_operator_detail(operator.id)

    def save_operator_detail(self, operator_no):
        data = self.get_json_data('char/data', operator_no)
        if data:
            materials = [item['material_id'] for item in database.material.get_all_material()]
            operator_id = database.operator.get_operator_id(operator_no)
            used_materials = []

            # todo 保存干员精英化信息
            evolve_cost = []
            for index, phases in enumerate(data['phases']):
                if phases['evolveCost']:
                    for item in phases['evolveCost']:
                        evolve_cost.append({
                            'operator_id': operator_id,
                            'evolve_level': index,
                            'use_material_id': item['id'],
                            'use_number': item['count']
                        })
                        if item['id'] not in used_materials:
                            used_materials.append(item['id'])
            if evolve_cost:
                database.operator.add_operator_evolve_costs(evolve_cost)
                print(' --- 精英化数据保存完毕...')

            # todo 保存干员技能信息
            skills = []
            skills_cost = {}
            for index, item in enumerate(data['skills']):
                detail = self.get_json_data('skills', item['skillId'])
                if detail:
                    name = detail['levels'][0]['name']
                    sk_no = item['skillId']

                    for lev, cond in enumerate(item['levelUpCostCond']):
                        if bool(cond['levelUpCost']) is False:
                            continue

                        if sk_no not in skills_cost:
                            skills_cost[sk_no] = []

                        for idx, cost in enumerate(cond['levelUpCost']):
                            skills_cost[sk_no].append({
                                'mastery_level': lev + 1,
                                'use_material_id': cost['id'],
                                'use_number': cost['count']
                            })
                            if cost['id'] not in used_materials:
                                used_materials.append(cost['id'])

                    skills.append({
                        'operator_id': operator_id,
                        'skill_no': sk_no,
                        'skill_index': index + 1,
                        'skill_name': name
                    })
            if skills:
                database.operator.add_operator_skill(skills)
                print(' --- 技能数据保存完毕...')

            # todo 保存干员技能专精信息
            skills_cost_list = []
            for sk_no, sk_list in skills_cost.items():
                skill_id = database.operator.get_skill_id(sk_no, operator_id)
                for item in sk_list:
                    item['skill_id'] = skill_id
                    skills_cost_list.append(item)
            if skills_cost_list:
                database.operator.add_operator_skill_mastery_costs(skills_cost_list)
                print(' --- 技能专精数据保存完毕...')

            # todo 保存未保存过的材料信息
            unsaved_materials = []
            unsaved_materials_drop = []
            for item in used_materials:
                if int(item) not in materials:
                    material_data = self.get_json_data('item', item)
                    icon_name = material_data['iconId']
                    unsaved_materials.append({
                        'material_id': item,
                        'material_name': material_data['name'].strip(),
                        'material_nickname': icon_name
                    })
                    self.get_pic(icon_name, 'materials')
            if unsaved_materials:
                database.material.add_material(unsaved_materials)
                print(' --- 材料数据保存完毕...')

    def update(self):
        t_record = millisecond()
        new_id = self.get_key()

        if bool(new_id) is False:
            return False

        data = self.get_operators_list(new_id)

        if bool(data) is False:
            return False

        not_exist = 0
        exist_operators = [item['operator_no'] for item in database.operator.get_all_operator()]
        for index, item in enumerate(data):
            operator = Operator(item)
            if operator.id not in exist_operators:
                record = millisecond()
                print('[%d/%d] 检测到未保存的干员【%s】，开始抓取数据...' % (index + 1, len(data), operator.name))

                self.save_operator_data(item)
                not_exist += 1

                print(' --- 抓取完毕。耗时 %d ms' % (millisecond() - record))

        message = '更新执行完毕，共更新了 %d 个干员，总耗时 %d ms' % (not_exist, millisecond() - t_record)

        print(message)
        return message


def millisecond():
    return int(time.time() * 1000)
