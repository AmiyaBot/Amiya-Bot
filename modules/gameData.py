import re
import os
import time
import json
import requests

from database.baseController import BaseController
from modules.commonMethods import remove_xml_tag

database = BaseController()

with open('resource/config/update_config.json', encoding='utf-8', mode='r')as file:
    update_config = json.load(file)

high_star = update_config['high_star']
classes = update_config['classes']
types = update_config['types']
limit = update_config['limit'] + update_config['linkage']
unavailable = [item for item in
               update_config['unavailable']['not_normally'] +
               update_config['unavailable']['sale_only'] +
               update_config['unavailable']['recruit_only'] +
               update_config['unavailable']['activity_only'] +
               update_config['unavailable']['contract_only'] +
               update_config['unavailable']['roguelike_only'] +
               update_config['unavailable']['linkage_only']]

formatter = {
    '0%': lambda v: str(abs(round(v * 100))) + '%'
}


class Operator:
    def __init__(self, data):
        self.id = data['No']
        self.name = data['name'] if data['No'] != 'char_1001_amiya2' else '阿米娅近卫'
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
        self.github_source = 'https://cdn.jsdelivr.net/gh/Kengxxiao/ArknightsGameData@master/zh_CN/gamedata/excel'
        self.data_source = 'https://andata.somedata.top/data-2020'
        self.pics_source = 'https://andata.somedata.top/dataX'
        self.pics_path = 'resource/images'

    def get_key(self, source):
        url = 'https://api.kokodayo.fun/api/base/info'
        info = requests.get(url, headers=self.headers)

        if info.status_code != 200:
            return False

        info = info.json()
        if 'result' not in info or not info['result']:
            return False

        result = info['result']
        for item in source.split('.'):
            if item in result:
                result = result[item]
            else:
                return False

        return result['key']

    def get_json_data(self, title='', name='', url=''):
        url = url or '%s/%s/%s.json' % (self.data_source, title, name)
        stream = requests.get(url, headers=self.headers, stream=True)
        if stream.status_code == 200:
            content = json.loads(stream.content)
            return content

    def get_pic(self, name, _type, _param=''):
        url = '%s/%s.png%s' % (self.pics_source, name, _param)
        path = '%s/%s/%s.png' % (self.pics_path, _type, name.split('/')[-1])
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

    def save_operator_data(self, operator):
        rarity = operator.rarity

        # todo 保存基础信息
        database.operator.add_operator([{
            'operator_no': operator.id,
            'operator_name': operator.name,
            'operator_en_name': operator.en_name,
            'operator_rarity': rarity,
            'operator_avatar': operator.id,
            'operator_class': operator.classes_code,
            'available': 1 if rarity >= 2 and operator.name not in unavailable else 0,
            'in_limit': 1 if operator.name in limit else 0
        }])
        self.get_pic('char/profile/' + operator.id, 'avatars')

        # todo 若此干员为可公招的干员，保存Tags信息
        if operator.recruit:
            operator_tags = OperatorTags(operator.name, rarity)
            operator_tags.append(operator.classes)
            operator_tags.append(operator.type)

            if str(rarity) in high_star:
                operator_tags.append(high_star[str(rarity)])

            for tag in operator.tags:
                operator_tags.append(tag)

            database.operator.add_operator_tags_relation(operator_tags.tags)

        # todo 保存干员的详细信息
        operator_id = database.operator.get_operator_id(operator_no=operator.id)
        self.save_operator_detail(operator.id, operator_id)
        self.save_operator_voices(operator.id, operator_id)
        self.save_operator_stories(operator.id, operator_id)

    def save_operator_detail(self, operator_no, operator_id):
        data = self.get_json_data('char/data', operator_no)
        if data:

            # todo 保存详细信息
            attrs_data = data['phases'][-1]['attributesKeyFrames'][-1]
            attrs = attrs_data['data']
            max_level = attrs_data['level']
            detail = {
                'operator_id': operator_id,
                'operator_desc': remove_xml_tag(data['description']),
                'operator_usage': data['itemUsage'] or '',
                'operator_quote': data['itemDesc'] or '',
                'operator_token': data['tokenDesc'] if 'tokenDesc' in data else '',
                'max_level': '%s-%s' % (len(data['phases']) - 1, max_level),
                'max_hp': attrs['maxHp'],
                'attack': attrs['atk'],
                'defense': attrs['def'],
                'magic_resistance': attrs['magicResistance'],
                'cost': attrs['cost'],
                'block_count': attrs['blockCnt'],
                'attack_time': attrs['baseAttackTime'],
                'respawn_time': attrs['respawnTime']
            }
            database.operator.add_operator_detail([detail])

            # todo 保存天赋信息
            talents = []
            if data['talents']:
                for item in data['talents']:
                    max_item = item['candidates'][-1]
                    talents.append({
                        'operator_id': operator_id,
                        'talents_name': max_item['name'],
                        'talents_desc': remove_xml_tag(max_item['description'])
                    })
                if talents:
                    database.operator.add_operator_talents(talents)

            # todo 保存基建信息
            building_skill = []
            if data['buildingData']:
                for item in data['buildingData']:
                    if item:
                        for bs in item:
                            building_skill.append({
                                'operator_id': operator_id,
                                'bs_unlocked': bs['cond']['phase'],
                                'bs_name': bs['data']['buffName'],
                                'bs_desc': remove_xml_tag(bs['data']['description'])
                            })
                if building_skill:
                    database.operator.add_operator_building_skill(building_skill)

            # todo 保存潜能信息
            potential = []
            if data['potentialRanks']:
                for index, item in enumerate(data['potentialRanks']):
                    potential.append({
                        'operator_id': operator_id,
                        'potential_desc': item['description'],
                        'potential_rank': index + 1
                    })
                if potential:
                    database.operator.add_operator_potential(potential)

            # todo 保存精英化信息
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
            if evolve_cost:
                database.operator.add_operator_evolve_costs(evolve_cost)

            # todo 保存技能信息
            skills = []
            skills_id = []
            skills_desc = {}
            skills_cost = {}
            for index, item in enumerate(data['skills']):
                detail = self.get_json_data('skills', item['skillId'])
                if detail:
                    name = detail['levels'][0]['name']
                    sk_no = item['skillId']

                    skills_id.append(sk_no)

                    if sk_no not in skills_desc:
                        skills_desc[sk_no] = []
                    if sk_no not in skills_cost:
                        skills_cost[sk_no] = []

                    # 预处理技能描述数据
                    for lev, desc in enumerate(detail['levels']):
                        blackboard = {item['key']: item['value'] for index, item in enumerate(desc['blackboard'])}
                        description = remove_xml_tag(desc['description'])
                        format_str = re.findall(r'({(\S+?)})', description)
                        if format_str:
                            for desc_item in format_str:
                                key = desc_item[1].split(':')
                                fd = key[0].lower().strip('-')
                                if fd in blackboard:
                                    value = blackboard[fd]
                                    if len(key) >= 2 and key[1] in formatter:
                                        value = formatter[key[1]](value)
                                    description = description.replace(desc_item[0], str(value))

                        skills_desc[sk_no].append({
                            'skill_level': lev + 1,
                            'skill_type': desc['skillType'],
                            'sp_type': desc['spData']['spType'],
                            'sp_init': desc['spData']['initSp'],
                            'sp_cost': desc['spData']['spCost'],
                            'duration': desc['duration'],
                            'description': description,
                            'max_charge': desc['spData']['maxChargeTime']
                        })

                    # 预处理专精数据
                    for lev, cond in enumerate(item['levelUpCostCond']):
                        if bool(cond['levelUpCost']) is False:
                            continue

                        for idx, cost in enumerate(cond['levelUpCost']):
                            skills_cost[sk_no].append({
                                'mastery_level': lev + 1,
                                'use_material_id': cost['id'],
                                'use_number': cost['count']
                            })

                    icon = 'skill_icon_' + (detail['iconId'] or detail['skillId'])
                    skills.append({
                        'operator_id': operator_id,
                        'skill_no': sk_no,
                        'skill_index': index + 1,
                        'skill_name': name,
                        'skill_icon': icon
                    })
                    self.get_pic('skills/pics/' + icon, 'skills')
            if skills:
                database.operator.add_operator_skill(skills)

            skills_id = {sk_no: database.operator.get_skill_id(sk_no, operator_id) for sk_no in skills_id}

            # todo 保存技能描述和专精信息
            todo_list = [
                ('技能描述', skills_desc, database.operator.add_operator_skill_description),
                ('技能专精信息', skills_cost, database.operator.add_operator_skill_mastery_costs)
            ]
            for todo in todo_list:
                save_list = []
                for sk_no, sk_list in todo[1].items():
                    for item in sk_list:
                        item['skill_id'] = skills_id[sk_no]
                        save_list.append(item)
                if save_list:
                    todo[2](save_list)

    def save_operator_voices(self, operator_no, operator_id):
        data = self.get_json_data('char/words', operator_no)
        if data:
            voices = []
            for item in data:
                voices.append({
                    'operator_id': operator_id,
                    'voice_title': item['voiceTitle'],
                    'voice_text': item['voiceText'],
                    'voice_no': item['voiceAsset']
                })
            if voices:
                database.operator.add_operator_voice(voices)

    def save_operator_stories(self, operator_no, operator_id):
        data = self.get_json_data('char/info', operator_no)
        if data:
            stories = []
            for item in data['storyTextAudio']:
                stories.append({
                    'operator_id': operator_id,
                    'story_title': item['storyTitle'],
                    'story_text': item['stories'][0]['storyText']
                })
            if stories:
                database.operator.add_operator_stories(stories)

    def update_operators(self, refresh=False):
        print('开始执行干员更新...')

        if refresh:
            database.operator.delete_all_data()
            print('已删除所有干员历史数据...')

        t_record = millisecond()
        char_key = self.get_key('agent.char')

        if bool(char_key) is False:
            return False

        data = self.get_operators_list(char_key)

        if bool(data) is False:
            return False

        not_exist = 0
        exist_operators = [item['operator_no'] for item in database.operator.get_all_operator()]
        for index, item in enumerate(data):
            operator = Operator(item)
            if operator.id not in exist_operators:
                record = millisecond()
                print('[%d/%d] 检测到未保存的干员【%s】，开始抓取数据...' % (index + 1, len(data), operator.name))

                self.save_operator_data(operator)
                not_exist += 1

                print(' --- 保存完毕。耗时 %d ms' % (millisecond() - record))

        message = '更新执行完毕，共更新了 %d 个干员，总耗时 %d ms' % (not_exist, millisecond() - t_record)
        print(message)
        return message

    def update_materials(self, refresh=False, use_cache=True):
        print('开始执行材料更新...')

        if refresh:
            database.material.delete_all_data()
            print('已删除所有材料历史数据...')

        item_data = {
            'building_data': {
                'url': '%s/building_data.json' % self.github_source,
                'file': 'resource/data/building_data.json'
            },
            'item_table': {
                'url': '%s/item_table.json' % self.github_source,
                'file': 'resource/data/item_table.json'
            }
        }

        for name, data_item in item_data.items():
            if os.path.exists(data_item['file']) is False or not use_cache:
                print('正在下载数据【%s】...' % name)
                data = self.get_json_data(url=data_item['url'])
                with open(data_item['file'], mode='w+', encoding='utf-8')as df:
                    df.write(json.dumps(data, ensure_ascii=False))
            else:
                print('数据【%s】已存在' % name)

        with open(item_data['building_data']['file'], mode='r', encoding='utf-8') as building_data:
            building_data = json.load(building_data)
            formulas = {
                'WORKSHOP': building_data['workshopFormulas'],
                'MANUFACTURE': building_data['manufactFormulas']
            }

        materials = []
        materials_made = []
        materials_source = []
        with open(item_data['item_table']['file'], mode='r', encoding='utf-8') as item_table:
            item_table = json.load(item_table)
            for item_id, item in item_table['items'].items():
                if item_id.isdigit():
                    material_name = item['name'].strip()
                    icon_name = item['iconId']
                    materials.append({
                        'material_id': item_id,
                        'material_name': material_name,
                        'material_icon': icon_name,
                        'material_desc': item['usage']
                    })
                    self.get_pic('item/pic/' + icon_name, 'materials')

                    for drop in item['stageDropList']:
                        materials_source.append({
                            'material_id': item_id,
                            'source_place': drop['stageId'],
                            'source_rate': drop['occPer']
                        })

                    for build in item['buildingProductList']:
                        if build['roomType'] in formulas and build['formulaId'] in formulas[build['roomType']]:
                            build_cost = formulas[build['roomType']][build['formulaId']]['costs']
                            for build_item in build_cost:
                                materials_made.append({
                                    'material_id': item_id,
                                    'use_material_id': build_item['id'],
                                    'use_number': build_item['count'],
                                    'made_type': build['roomType']
                                })

                    print('材料【%s】数据构建完成...' % material_name)

        if materials:
            database.material.add_material(materials)
        if materials_made:
            database.material.add_material_made(materials_made)
        if materials_source:
            database.material.add_material_source(materials_source)

        message = '更新执行完毕，共 %d 个材料' % len(materials)
        print(message)
        return message

    def update_stage(self):
        print('开始执行地图更新...')

        stage_key = self.get_key('level.stage')
        stage_data = self.get_json_data('lists/stage', stage_key)
        stage_list = []

        def loop_list(data):
            nonlocal stage_list
            for i, item in (enumerate(data) if type(data) is list else data.items()):
                item_type = type(item)
                if item_type is list:
                    loop_list(item)
                elif item_type is dict and 'type' in item and item['type'] == 'sub':
                    loop_list(item['data'])
                elif item_type is str:
                    item = re.split(r'\s+', item)
                    if item[0]:
                        stage_list.append({
                            'stage_id': item[2],
                            'stage_code': item[0],
                            'stage_name': item[1]
                        })

        for index, stage in stage_data.items():
            loop_list(stage)

        database.material.update_stage(stage_list)

        message = '更新执行完毕，共 %d 张地图' % len(stage_list)
        print(message)
        return message


def millisecond():
    return int(time.time() * 1000)
