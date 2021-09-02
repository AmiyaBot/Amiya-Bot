import re

from core.util.common import remove_punctuation, remove_xml_tag

from .builder import Operator
from .sourceBank import SourceBank
from .updateConfig import Config


class DataSource(SourceBank):
    def __init__(self, auto_update=True, check_assets=True):
        super().__init__()
        self.download_resource(not auto_update)
        self.download_bot_resource()
        self.download_bot_console()
        self.wiki.download_self_voices()

        self.operators = self.init_operators()
        self.enemies = self.init_enemies()
        self.stages = self.init_stages()

        self.materials, self.materials_map, self.materials_made, self.materials_source = self.init_materials()

        if check_assets:
            self.download_operators_photo(self.operators)
            self.download_materials_icon(self.materials)
            self.download_enemies_photo(self.enemies)

    def get_recruit_operators(self):
        recruit_detail = remove_xml_tag(self.get_json_data('gacha_table')['recruitDetail'])
        recruit_group = re.findall(r'★\\n(.*)', recruit_detail)
        recruit_operators = []

        for item in recruit_group:
            recruit_operators += item.replace(' ', '').split('/')

        return recruit_operators

    def init_operators(self):
        recruit_operators = self.get_recruit_operators()
        operators_list = self.get_json_data('character_table')
        operators_patch_list = self.get_json_data('char_patch_table')['patchChars']
        voice_data = self.get_json_data('charword_table')
        skins_data = self.get_json_data('skin_table')['charSkins']

        operators_list.update(operators_patch_list)

        operators = []
        voice_map = {}
        skins_map = {}

        map_data = (
            (voice_data, voice_map, 'wordKey'),
            (skins_data, skins_map, 'charId')
        )

        for map_item in map_data:
            for n, item in map_item[0].items():
                char_id = item[map_item[-1]]
                if char_id not in map_item[1]:
                    map_item[1][char_id] = []

                map_item[1][char_id].append(item)

        for code, item in operators_list.items():
            if item['profession'] not in Config.classes:
                continue

            operators.append(
                Operator(
                    parent=self,
                    code=code,
                    data=item,
                    voice_list=voice_map[code] if code in voice_map else [],
                    skins_list=skins_map[code] if code in skins_map else [],
                    is_recruit=item['name'] in recruit_operators
                )
            )

        return {remove_punctuation(item.name): item for item in operators}

    def init_materials(self):
        building_data = self.get_json_data('building_data')
        item_data = self.get_json_data('item_table')
        formulas = {
            'WORKSHOP': building_data['workshopFormulas'],
            'MANUFACTURE': building_data['manufactFormulas']
        }

        materials = {}
        materials_map = {}
        materials_made = {}
        materials_source = {}
        for item_id, item in item_data['items'].items():
            if 'p_char' in item_id:
                continue

            material_name = item['name'].strip()
            icon_name = item['iconId']

            materials[item_id] = {
                'material_id': item_id,
                'material_name': material_name,
                'material_icon': icon_name,
                'material_desc': item['usage']
            }
            materials_map[material_name] = item_id

            for drop in item['stageDropList']:
                if item_id not in materials_source:
                    materials_source[item_id] = {}
                materials_source[item_id][drop['stageId']] = {
                    'material_id': item_id,
                    'source_place': drop['stageId'],
                    'source_rate': drop['occPer']
                }

            for build in item['buildingProductList']:
                if build['roomType'] in formulas and build['formulaId'] in formulas[build['roomType']]:
                    build_cost = formulas[build['roomType']][build['formulaId']]['costs']
                    for build_item in build_cost:
                        if item_id not in materials_made:
                            materials_made[item_id] = []
                        materials_made[item_id].append({
                            'material_id': item_id,
                            'use_material_id': build_item['id'],
                            'use_number': build_item['count'],
                            'made_type': build['roomType']
                        })

        return materials, materials_map, materials_made, materials_source

    def init_enemies(self):
        enemies_info = self.get_json_data('enemy_handbook_table')
        enemies_data = self.get_json_data('enemy_database')['enemies']

        data = {}
        for item in enemies_data:
            if item['Key'] in enemies_info:
                info = enemies_info[item['Key']]
                data[info['name']] = {
                    'info': info,
                    'data': item['Value']
                }

        return data

    def init_stages(self):
        stage_data = self.get_json_data('stage_table')['stages']
        stage_list = {}

        for stage_id, item in stage_data.items():
            if '#f#' not in stage_id and item['name']:
                stage_list[stage_id] = {
                    'stage_id': stage_id,
                    'stage_code': item['code'],
                    'stage_name': item['name']
                }

        return stage_list

    def download_operators_photo(self, operators):
        for index, name in enumerate(operators.keys()):
            item = operators[name]
            idx = f'{index + 1}/{len(operators.keys())}'

            self.get_pic('char/profile/' + item.id, 'avatars', _index=idx)
            self.get_pic('char/halfPic/%s_1' % item.id, 'photo', '?x-oss-process=style/small-test', _index=idx)

            skills_list = item.skills()[0]
            for skill in skills_list:
                self.get_pic('skills/pics/' + skill['skill_icon'], 'skills', _index=idx)

            skins_list = item.skins()
            for skin in skins_list:
                self.get_pic('char/set/' + skin['skin_image'], 'picture', _index=idx)

    def download_materials_icon(self, materials):
        for index, m_id in enumerate(materials.keys()):
            item = materials[m_id]
            idx = f'{index + 1}/{len(materials.keys())}'

            self.get_pic(
                name='item/pic/' + item['material_icon'],
                _wiki='道具_带框_' + item['material_name'],
                _type='materials',
                _index=idx
            )

    def download_enemies_photo(self, enemies):
        for index, name in enumerate(enemies.keys()):
            item = enemies[name]
            idx = f'{index + 1}/{len(enemies.keys())}'

            self.get_pic(
                name='enemy/pic/' + item['info']['enemyId'],
                _type='enemy',
                _param='?x-oss-process=style/jpg-test',
                _index=idx
            )
