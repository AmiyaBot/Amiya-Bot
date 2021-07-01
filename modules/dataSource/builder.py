import re

from modules.commonMethods import remove_xml_tag
from modules.dataSource.updateConfig import Config
from modules.dataSource.sourceBank import SourceBank

formatter = {
    '0%': lambda v: str(abs(round(v * 100))) + '%'
}


class Operator(SourceBank):
    def __init__(self, code, data, voice_list, skins_list, recruit=False):
        super().__init__()

        self.id = code
        self.name = data['name']
        self.en_name = data['appellation']
        self.rarity = data['rarity'] + 1
        self.classes = Config.classes[data['profession']]
        self.classes_code = list(Config.classes.keys()).index(data['profession']) + 1
        self.type = Config.types[data['position']]
        self.tags = data['tagList']
        self.recruit = recruit

        self.voice_list = voice_list
        self.skins_list = skins_list

        # todo 阿米娅近卫
        if code == 'char_1001_amiya2':
            self.name = '阿米娅近卫'
            self.en_name = 'AmiyaGuard'

        # todo 小车
        if code in ['char_285_medic2', 'char_286_cast3', 'char_376_therex']:
            self.tags.append('机械支援')

        self.data = data

    def detail(self, operator_id):
        items = self.get_json_data('item_table')['items']

        token_id = 'p_' + self.id
        token = None
        if token_id in items:
            token = items[token_id]

        max_phases = self.data['phases'][-1]
        max_attr = max_phases['attributesKeyFrames'][-1]['data']

        detail = {
            'operator_id': operator_id,
            'operator_desc': remove_xml_tag(self.data['description']),
            'operator_usage': self.data['itemUsage'] or '',
            'operator_quote': self.data['itemDesc'] or '',
            'operator_token': token['description'] if token else '',
            'max_level': '%s-%s' % (len(self.data['phases']) - 1, max_phases['maxLevel']),
            'max_hp': max_attr['maxHp'],
            'attack': max_attr['atk'],
            'defense': max_attr['def'],
            'magic_resistance': max_attr['magicResistance'],
            'cost': max_attr['cost'],
            'block_count': max_attr['blockCnt'],
            'attack_time': max_attr['baseAttackTime'],
            'respawn_time': max_attr['respawnTime']
        }

        return detail

    def talents(self, operator_id):
        talents = []
        if self.data['talents']:
            for item in self.data['talents']:
                max_item = item['candidates'][-1]
                talents.append({
                    'operator_id': operator_id,
                    'talents_name': max_item['name'],
                    'talents_desc': remove_xml_tag(max_item['description'])
                })

        return talents

    def potential(self, operator_id):
        potential = []
        if self.data['potentialRanks']:
            for index, item in enumerate(self.data['potentialRanks']):
                potential.append({
                    'operator_id': operator_id,
                    'potential_desc': item['description'],
                    'potential_rank': index + 1
                })

        return potential

    def evolve_costs(self, operator_id):
        evolve_cost = []
        for index, phases in enumerate(self.data['phases']):
            if phases['evolveCost']:
                for item in phases['evolveCost']:
                    evolve_cost.append({
                        'operator_id': operator_id,
                        'evolve_level': index,
                        'use_material_id': item['id'],
                        'use_number': item['count']
                    })

        return evolve_cost

    def skills(self, operator_id):
        skill_data = self.get_json_data('skill_table')

        skills = []
        skills_id = []
        skills_desc = {}
        skills_cost = {}
        for index, item in enumerate(self.data['skills']):
            code = item['skillId']
            detail = skill_data[code]
            icon = 'skill_icon_' + (detail['iconId'] or detail['skillId'])

            if bool(detail) is False:
                continue

            skills_id.append(code)

            if code not in skills_desc:
                skills_desc[code] = []
            if code not in skills_cost:
                skills_cost[code] = []

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

                skills_desc[code].append({
                    'skill_level': lev + 1,
                    'skill_type': desc['skillType'],
                    'sp_type': desc['spData']['spType'],
                    'sp_init': desc['spData']['initSp'],
                    'sp_cost': desc['spData']['spCost'],
                    'duration': desc['duration'],
                    'description': description,
                    'max_charge': desc['spData']['maxChargeTime']
                })

            for lev, cond in enumerate(item['levelUpCostCond']):
                if bool(cond['levelUpCost']) is False:
                    continue

                for idx, cost in enumerate(cond['levelUpCost']):
                    skills_cost[code].append({
                        'mastery_level': lev + 1,
                        'use_material_id': cost['id'],
                        'use_number': cost['count']
                    })

            skills.append({
                'operator_id': operator_id,
                'skill_no': code,
                'skill_index': index + 1,
                'skill_name': detail['levels'][0]['name'],
                'skill_icon': icon
            })

        return skills, skills_id, skills_cost, skills_desc

    def building_skills(self, operator_id):
        building_data = self.get_json_data('building_data')
        building_skills = building_data['buffs']

        skills = []
        if self.id in building_data['chars']:
            char_buff = building_data['chars'][self.id]
            for buff in char_buff['buffChar']:
                for item in buff['buffData']:
                    buff_id = item['buffId']
                    if buff_id in building_skills:
                        skill = building_skills[buff_id]
                        skills.append({
                            'operator_id': operator_id,
                            'bs_unlocked': item['cond']['phase'],
                            'bs_name': skill['buffName'],
                            'bs_desc': remove_xml_tag(skill['description'])
                        })

        return skills

    def voices(self, operator_id):
        voices = []
        for item in self.voice_list:
            voices.append({
                'operator_id': operator_id,
                'voice_title': item['voiceTitle'],
                'voice_text': item['voiceText'],
                'voice_no': item['voiceAsset']
            })

        return voices

    def stories(self, operator_id):
        stories_data = self.get_json_data('handbook_info_table')['handbookDict']
        stories = []
        if self.id in stories_data:
            for item in stories_data[self.id]['storyTextAudio']:
                stories.append({
                    'operator_id': operator_id,
                    'story_title': item['storyTitle'],
                    'story_text': item['stories'][0]['storyText']
                })
        return stories

    def skins(self, operator_id):
        skins = []
        for item in self.skins_list:
            if '@' not in item['skinId']:
                continue

            skin_key = item['avatarId'].split('#')
            skin_data = item['displaySkin']

            skin_image = f'{skin_key[0]}%23{skin_key[1]}'
            skin_type = 1

            skins.append({
                'operator_id': operator_id,
                'skin_image': skin_image,
                'skin_type': skin_type,
                'skin_name': skin_data['skinName'] or self.name,
                'skin_drawer': skin_data['drawerName'] or '',
                'skin_group': skin_data['skinGroupName'] or '',
                'skin_content': skin_data['dialog'] or '',
                'skin_usage': skin_data['usage'] or '',
                'skin_desc': skin_data['description'] or '',
                'skin_source': skin_data['obtainApproach'] or ''
            })

        return skins


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
