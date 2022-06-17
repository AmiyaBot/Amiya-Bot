import re

from core.util import remove_xml_tag, remove_punctuation, integer

from .common import ArknightsConfig, JsonData


def parse_template(blackboard, description):
    formatter = {
        '0%': lambda v: f'{round(v * 100)}%'
    }
    data_dict = {item['key']: item['value'] for index, item in enumerate(blackboard)}
    desc = remove_xml_tag(description.replace('>-{', '>{'))
    format_str = re.findall(r'({(\S+?)})', desc)
    if format_str:
        for desc_item in format_str:
            key = desc_item[1].split(':')
            fd = key[0].lower().strip('-')
            if fd in data_dict:
                value = integer(data_dict[fd])

                if len(key) >= 2 and key[1] in formatter:
                    value = formatter[key[1]](value)

                desc = desc.replace(desc_item[0], f' [cl {value}@#174CC6 cle] ')

    return desc


def build_range(grids):
    _max = [0, 0, 0, 0]
    for item in [{'row': 0, 'col': 0}] + grids:
        row = item['row']
        col = item['col']
        if row <= _max[0]:
            _max[0] = row
        if row >= _max[1]:
            _max[1] = row
        if col <= _max[2]:
            _max[2] = col
        if col >= _max[3]:
            _max[3] = col

    width = abs(_max[2]) + _max[3] + 1
    height = abs(_max[0]) + _max[1] + 1

    empty = '　'
    block = '□'
    origin = '■'

    range_map = []
    for h in range(height):
        range_map.append([empty for _ in range(width)])

    for item in grids:
        x = abs(_max[0]) + item['row']
        y = abs(_max[2]) + item['col']
        range_map[x][y] = block
    range_map[abs(_max[0])][abs(_max[2])] = origin

    return ''.join([''.join(item) + '\n' for item in range_map])


class Operator:
    def __init__(self, code, data, voice_list, skins_list, is_recruit=False):
        sub_classes = JsonData.get_json_data('uniequip_table')['subProfDict']
        range_data = JsonData.get_json_data('range_table')
        nation_id = JsonData.get_json_data('character_table')
        drawer_id = JsonData.get_json_data('skin_table')['charSkins']
        range_id = data['phases'][-1]['rangeId']
        range_map = '无范围'
        if range_id in range_data:
            range_map = build_range(range_data[range_id]['grids'])

        self.id = code
        self.name = data['name']
        self.en_name = data['appellation']
        self.wiki_name = data['name']
        self.index_name = remove_punctuation(data['name'])
        self.rarity = data['rarity'] + 1
        self.classes = ArknightsConfig.classes[data['profession']]
        self.classes_sub = sub_classes[data['subProfessionId']]['subProfessionName']
        self.classes_code = data['profession']
        self.type = ArknightsConfig.types[data['position']]
        self.tags = data['tagList']
        self.range = range_map
        self.birthday = ''
        self.nation = nation_id[code]["nationId"]
        self.drawer_name = drawer_id[code+'#1' if code != 'char_1001_amiya2' else code + '#2']["displaySkin"]["drawerName"]
        self.limit = self.name in ArknightsConfig.limit
        self.unavailable = self.name in ArknightsConfig.unavailable

        self.is_recruit = is_recruit

        self.voice_list = voice_list
        self.skins_list = sorted(skins_list, key=lambda n: n['displaySkin']['getTime'])

        self.__tags()
        self.__extra()

        self.data = data

    def __str__(self):
        return f'{self.id}_{self.name}'

    def __repr__(self):
        return f'{self.id}_{self.name}'

    def detail(self):
        items = JsonData.get_json_data('item_table')['items']

        token_id = 'p_' + self.id
        token = None
        if token_id in items:
            token = items[token_id]

        max_phases = self.data['phases'][-1]
        max_attr = max_phases['attributesKeyFrames'][-1]['data']

        trait = remove_xml_tag(self.data['description'])
        if self.data['trait']:
            max_trait = self.data['trait']['candidates'][-1]
            trait = parse_template(max_trait['blackboard'], max_trait['overrideDescripton'] or trait)

        detail = {
            'operator_trait': trait.replace('\\n', '\n'),
            'operator_usage': self.data['itemUsage'] or '',
            'operator_quote': self.data['itemDesc'] or '',
            'operator_token': token['description'] if token else '',
            'max_level': '%s - %s' % (len(self.data['phases']) - 1, max_phases['maxLevel'])
        }
        detail.update(max_attr)

        return detail, self.data['favorKeyFrames'][-1]['data']

    def talents(self):
        talents = []
        if self.data['talents']:
            for item in self.data['talents']:
                max_item = item['candidates'][-1]
                talents.append({
                    'talents_name': max_item['name'],
                    'talents_desc': remove_xml_tag(max_item['description'])
                })

        return talents

    def potential(self):
        potential = []
        if self.data['potentialRanks']:
            for index, item in enumerate(self.data['potentialRanks']):
                potential.append({
                    'potential_desc': item['description'],
                    'potential_rank': index + 1
                })

        return potential

    def evolve_costs(self):
        evolve_cost = []
        for index, phases in enumerate(self.data['phases']):
            if phases['evolveCost']:
                for item in phases['evolveCost']:
                    evolve_cost.append({
                        'evolve_level': index,
                        'use_material_id': item['id'],
                        'use_number': item['count']
                    })

        return evolve_cost

    def skills(self):
        skill_data = JsonData.get_json_data('skill_table')
        range_data = JsonData.get_json_data('range_table')

        skills = []
        skills_id = []
        skills_cost = []
        skills_desc = {}

        level_up_data = self.data['allSkillLvlup']
        if level_up_data:
            for index, item in enumerate(level_up_data):
                if item['lvlUpCost']:
                    for cost in item['lvlUpCost']:
                        skills_cost.append({
                            'skill_no': None,
                            'level': index + 2,
                            'mastery_level': 0,
                            'use_material_id': cost['id'],
                            'use_number': cost['count']
                        })

        for index, item in enumerate(self.data['skills']):
            code = item['skillId']

            if code not in skill_data:
                continue

            detail = skill_data[code]
            icon = 'skill_icon_' + (detail['iconId'] or detail['skillId'])

            if bool(detail) is False:
                continue

            skills_id.append(code)

            if code not in skills_desc:
                skills_desc[code] = []

            for lev, desc in enumerate(detail['levels']):
                description = parse_template(desc['blackboard'], desc['description'])

                skill_range = self.range
                if desc['rangeId'] in range_data:
                    skill_range = build_range(range_data[desc['rangeId']]['grids'])

                skills_desc[code].append({
                    'skill_level': lev + 1,
                    'skill_type': desc['skillType'],
                    'sp_type': desc['spData']['spType'],
                    'sp_init': desc['spData']['initSp'],
                    'sp_cost': desc['spData']['spCost'],
                    'duration': integer(desc['duration']),
                    'description': description.replace('\\n', '\n'),
                    'max_charge': desc['spData']['maxChargeTime'],
                    'range': skill_range
                })

            for lev, cond in enumerate(item['levelUpCostCond']):
                if bool(cond['levelUpCost']) is False:
                    continue

                for idx, cost in enumerate(cond['levelUpCost']):
                    skills_cost.append({
                        'skill_no': code,
                        'level': lev + 8,
                        'mastery_level': lev + 1,
                        'use_material_id': cost['id'],
                        'use_number': cost['count']
                    })

            skills.append({
                'skill_no': code,
                'skill_index': index + 1,
                'skill_name': detail['levels'][0]['name'],
                'skill_icon': icon
            })

        return skills, skills_id, skills_cost, skills_desc

    def building_skills(self):
        building_data = JsonData.get_json_data('building_data')
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
                            'bs_unlocked': item['cond']['phase'],
                            'bs_name': skill['buffName'],
                            'bs_desc': remove_xml_tag(skill['description'])
                        })

        return skills

    def voices(self):
        voices = []
        for item in self.voice_list:
            voices.append({
                'voice_title': item['voiceTitle'],
                'voice_text': item['voiceText'],
                'voice_no': item['voiceAsset']
            })

        return voices

    def stories(self):
        stories_data = JsonData.get_json_data('handbook_info_table')['handbookDict']
        stories = []
        if self.id in stories_data:
            for item in stories_data[self.id]['storyTextAudio']:
                stories.append({
                    'story_title': item['storyTitle'],
                    'story_text': item['stories'][0]['storyText']
                })
        return stories

    def skins(self):
        skins = []
        skin_sort = 0

        for item in self.skins_list:
            skin_data = item['displaySkin']
            skin_id = item['skinId']
            skin_lvl = {
                '1': ('初始', 'stage0'),
                '1+': ('精英一', 'stage1'),
                '2': ('精英二', 'stage2'),
            }

            skin_info = skin_id.split('#')
            skin_index = skin_info[1]

            skin_name = ''

            if '@' not in skin_id:
                skin_name, skin_key = skin_lvl[skin_index]
            else:
                skin_sort += 1
                skin_key = f'skin{skin_sort}'

            skins.append({
                'skin_id': skin_id,
                'skin_key': skin_key,
                'skin_name': skin_data['skinName'] or skin_name,
                'skin_drawer': skin_data['drawerName'] or '',
                'skin_group': skin_data['skinGroupName'] or '',
                'skin_content': skin_data['dialog'] or '',
                'skin_usage': skin_data['usage'] or skin_name + '立绘',
                'skin_desc': skin_data['description'] or '',
                'skin_source': skin_data['obtainApproach'] or ''
            })

        return skins

    def modules(self):
        equips = JsonData.get_json_data('uniequip_table')
        equips_battle = JsonData.get_json_data('battle_equip_table')

        equips_rel = equips['charEquip']
        modules_list = equips['equipDict']
        mission_list = equips['missionList']

        modules = []
        if self.id in equips_rel:
            for m_id in equips_rel[self.id]:
                module = modules_list[m_id]

                module['missions'] = []
                module['detail'] = equips_battle[m_id] if m_id in equips_battle else None

                for mission in module['missionList']:
                    module['missions'].append(mission_list[mission])

                modules.append(module)

        return modules

    def __tags(self):
        self.tags.append(self.classes)
        self.tags.append(self.type)
        if str(self.rarity) in ArknightsConfig.high_star:
            self.tags.append(ArknightsConfig.high_star[str(self.rarity)])

        if self.id in ['char_285_medic2', 'char_286_cast3', 'char_376_therex', 'char_4000_jnight']:
            self.tags.append('支援机械')

    def __extra(self):
        if self.id == 'char_1001_amiya2':
            self.name = '阿米娅近卫'
            self.en_name = 'AmiyaGuard'
            self.wiki_name = '阿米娅(近卫)'
