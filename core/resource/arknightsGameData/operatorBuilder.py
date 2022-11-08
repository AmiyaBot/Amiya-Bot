import re

from typing import Dict
from core.util import remove_xml_tag, remove_punctuation, integer

from .common import ArknightsConfig, JsonData, html_symbol


class Operator:
    def __init__(self, code: str, data: dict, is_recruit: bool = False):
        sub_classes = JsonData.get_json_data('uniequip_table')['subProfDict']
        character_table = JsonData.get_json_data('character_table')
        team_table = JsonData.get_json_data('handbook_team_table')
        item_table = JsonData.get_json_data('item_table')['items']

        self.data = data
        self.__voice_list = Collection.get_voice_list(code)
        self.__skins_list = sorted(Collection.get_skins_list(code), key=lambda n: n['displaySkin']['getTime'])

        data['name'] = data['name'].strip()

        self.id = code
        self.cv = {}

        self.type = ArknightsConfig.types.get(data['position'])
        self.tags = []
        self.range = '无范围'
        self.rarity = data['rarity'] + 1
        self.number = data['displayNumber']

        self.name = data['name']
        self.en_name = data['appellation']
        self.wiki_name = data['name']
        self.index_name = remove_punctuation(data['name'])
        self.origin_name = '未知'

        self.classes = ArknightsConfig.classes[data['profession']]
        self.classes_sub = sub_classes[data['subProfessionId']]['subProfessionName']
        self.classes_code = data['profession']

        self.race = '未知'
        self.drawer = '未知'
        self.team_id = data['teamId']
        self.team = team_table[self.team_id]['powerName'] if self.team_id in team_table else '未知'
        self.group_id = data['groupId']
        self.group = team_table[self.group_id]['powerName'] if self.group_id in team_table else '未知'
        self.nation_id = character_table[code]['nationId']
        self.nation = team_table[self.nation_id]['powerName'] if self.nation_id in team_table else '未知'
        self.birthday = '未知'

        self.profile = data['itemUsage'] or '无'
        self.impression = data['itemDesc'] or '无'

        self.potential_item = ''
        if data['potentialItemId'] in item_table:
            self.potential_item = item_table[data['potentialItemId']]['description']

        self.limit = self.name in ArknightsConfig.limit
        self.unavailable = self.name in ArknightsConfig.unavailable

        self.is_recruit = is_recruit
        self.is_sp = data['isSpChar']

        self.__cv()
        self.__race()
        self.__tags()
        self.__drawer()
        self.__range()
        self.__origin(character_table)
        self.__extra()

    def __str__(self):
        return f'{self.id}_{self.name}'

    def __repr__(self):
        return f'{self.id}_{self.name}'

    def dict(self):
        return {
            'name': self.name,
            'en_name': self.en_name,
            'rarity': self.rarity,
            'classes': self.classes,
            'classes_sub': self.classes_sub,
            'classes_code': self.classes_code,
            'type': self.type
        }

    def detail(self):
        items = JsonData.get_json_data('item_table')['items']

        token_id = 'p_' + self.id
        token = None
        if token_id in items:
            token = items[token_id]

        max_phases = self.data['phases'][-1]
        max_attr = max_phases['attributesKeyFrames'][-1]['data']

        trait = html_tag_format(self.data['description'])
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

    def tokens(self):
        token_list = []

        if self.data['tokenKey'] and self.data['tokenKey'] in Collection.tokens_map:
            token_list.append(Collection.tokens_map[self.data['tokenKey']])

        if self.data['skills']:
            for item in self.data['skills']:
                if item['overrideTokenKey'] and item['overrideTokenKey'] in Collection.tokens_map:
                    token_list.append(Collection.tokens_map[item['overrideTokenKey']])

        return [
            {
                'id': item.id,
                'type': item.type,
                'name': item.name,
                'en_name': item.en_name,
                'description': item.description,
                'attr': item.attr
            } for item in token_list
        ]

    def talents(self):
        talents = []
        if self.data['talents']:
            for item in self.data['talents']:
                max_item = item['candidates'][-1]
                talents.append({
                    'talents_name': max_item['name'],
                    'talents_desc': html_tag_format(max_item['description'])
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
                            'bs_icon': skill['skillIcon'],
                            'bs_name': skill['buffName'],
                            'bs_desc': html_tag_format(skill['description'])
                        })

        return skills

    def voices(self):
        voices = []
        for item in self.__voice_list:
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

        for item in self.__skins_list:
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
        tags = [self.classes, self.type]

        if self.id in ['char_285_medic2', 'char_286_cast3', 'char_376_therex', 'char_4000_jnight']:
            tags.append('支援机械')

        if str(self.rarity) in ArknightsConfig.high_star:
            tags.append(ArknightsConfig.high_star[str(self.rarity)])

        self.tags = self.data['tagList'] + tags

    def __cv(self):
        word_data = JsonData.get_json_data('charword_table')
        if self.id in word_data['voiceLangDict']:
            voice_lang = word_data['voiceLangDict'][self.id]['dict']
            self.cv = {
                word_data['voiceLangTypeDict'][name]['name']: item['cvName'] for name, item in voice_lang.items()
            }

    def __race(self):
        for story in self.stories():
            if story['story_title'] == '基础档案':
                r = re.search(r'\n【种族】.*?(\S+).*?\n', story['story_text'])
                if r:
                    self.race = str(r.group(1))
                break

    def __drawer(self):
        skins_list = self.skins()
        if skins_list:
            self.drawer = skins_list[0]['skin_drawer']

    def __range(self):
        range_data = JsonData.get_json_data('range_table')
        range_id = self.data['phases'][-1]['rangeId']
        if range_id in range_data:
            self.range = build_range(range_data[range_id]['grids'])

    def __origin(self, character):
        sp_char = JsonData.get_json_data('char_meta_table')['spCharGroups']
        for oid, group in sp_char.items():
            for item in group:
                if item == self.id:
                    self.origin_name = character[oid]['name']

    def __extra(self):
        if self.id == 'char_1001_amiya2':
            self.name = '阿米娅近卫'
            self.en_name = 'AmiyaGuard'
            self.wiki_name = '阿米娅(近卫)'
            self.origin_name = '阿米娅'


class Token:
    def __init__(self, code: str, data: dict):
        range_data = JsonData.get_json_data('range_table')

        self.id = code
        self.name = data['name']
        self.en_name = data['appellation']
        self.description = html_tag_format(data['description'] or '')
        self.classes = ArknightsConfig.token_classes.get(data['profession'])
        self.type = ArknightsConfig.types.get(data['position'])
        self.attr = []

        if data['phases']:
            for evolve, item in enumerate(data['phases']):
                range_id = item['rangeId']
                range_map = '无范围'
                if range_id in range_data:
                    range_map = build_range(range_data[range_id]['grids'])

                self.attr.append(
                    {
                        'evolve': evolve,
                        'range': range_map,
                        'attr': item['attributesKeyFrames']
                    }
                )

    def __str__(self):
        return f'{self.id}_{self.name}'

    def __repr__(self):
        return f'{self.id}_{self.name}'


class Collection:
    voice_map: dict = {}
    skins_map: dict = {}
    tokens_map: Dict[str, Token] = {}

    @classmethod
    def get_voice_list(cls, code):
        return cls.voice_map.get(code, [])

    @classmethod
    def get_skins_list(cls, code):
        return cls.skins_map.get(code, [])


def html_tag_format(text):
    for o, f in html_symbol.items():
        text = text.replace(o, f)

    return remove_xml_tag(text)


def parse_template(blackboard, description):
    formatter = {
        '0%': lambda v: f'{round(v * 100)}%'
    }
    data_dict = {item['key']: item['value'] for index, item in enumerate(blackboard)}

    desc = html_tag_format(description.replace('>-{', '>{'))
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
