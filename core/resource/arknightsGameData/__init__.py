import os
import re

from typing import List, Dict, Tuple
from core.network.download import download_sync
from core.resource import resource_config
from core.util import remove_xml_tag, remove_punctuation, create_dir, singleton, sorted_dict
from core import log

from .common import ArknightsConfig, JsonData
from .operatorBuilder import Operator

STAGES = Dict[str, Dict[str, str]]
ENEMIES = Dict[str, Dict[str, dict]]
OPERATORS = Tuple[
    Dict[str, Operator],
    Dict[str, Dict[str, List[Operator]]]
]
MATERIALS = Tuple[
    Dict[str, Dict[str, str]],
    Dict[str, str],
    Dict[str, List[Dict[str, str]]],
    Dict[str, Dict[str, str]]
]


def init_operators() -> OPERATORS:
    recruit_detail = remove_xml_tag(JsonData.get_json_data('gacha_table')['recruitDetail'])
    recruit_group = re.findall(r'★\\n(.*)', recruit_detail)
    recruit_operators = []

    for item in recruit_group:
        recruit_operators += item.replace(' ', '').split('/')

    operators_list = JsonData.get_json_data('character_table')
    operators_patch_list = JsonData.get_json_data('char_patch_table')['patchChars']
    voice_data = JsonData.get_json_data('charword_table')
    skins_data = JsonData.get_json_data('skin_table')['charSkins']

    operators_list.update(operators_patch_list)

    voice_map = {}
    skins_map = {}

    map_data = (
        (voice_data, voice_map, 'wordKey'),
        (skins_data, skins_map, 'charId')
    )

    for map_item in map_data:
        data = map_item[0]
        if 'charWords' in data:
            data = data['charWords']
        for n, item in data.items():
            char_id = item[map_item[-1]]
            if char_id not in map_item[1]:
                map_item[1][char_id] = []

            map_item[1][char_id].append(item)

    operators: List[Operator] = []
    birth = {}

    for code, item in operators_list.items():
        if item['profession'] not in ArknightsConfig.classes:
            continue

        operators.append(
            Operator(
                code=code,
                data=item,
                voice_list=voice_map[code] if code in voice_map else [],
                skins_list=skins_map[code] if code in skins_map else [],
                is_recruit=item['name'] in recruit_operators
            )
        )

    for item in operators:
        for story in item.stories():
            if story['story_title'] == '基础档案':
                r = re.search(r'\n【(生日|出厂日)】.*?(\d+)月(\d+)日\n', story['story_text'])
                if r:
                    month = int(r.group(2))
                    day = int(r.group(3))

                    if month not in birth:
                        birth[month] = {}
                    if day not in birth[month]:
                        birth[month][day] = []

                    item.birthday = f'{month}月{day}日'
                    birth[month][day].append(item)
                break

    birthdays = {}
    for month, days in birth.items():
        birthdays[month] = sorted_dict(days)
    birthdays = sorted_dict(birthdays)

    return {remove_punctuation(item.name): item for item in operators}, birthdays


def init_materials() -> MATERIALS:
    building_data = JsonData.get_json_data('building_data')
    item_data = JsonData.get_json_data('item_table')
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


def init_enemies() -> ENEMIES:
    enemies_info = JsonData.get_json_data('enemy_handbook_table')
    enemies_data = JsonData.get_json_data('enemy_database')['enemies']

    data = {}
    for item in enemies_data:
        if item['Key'] in enemies_info:
            info = enemies_info[item['Key']]
            data[info['name'].lower()] = {
                'info': info,
                'data': item['Value']
            }

    return data


def init_stages() -> STAGES:
    stage_data = JsonData.get_json_data('stage_table')['stages']
    stage_list = {}

    for stage_id, item in stage_data.items():
        if '#f#' not in stage_id and item['name']:
            stage_list[stage_id] = {
                'stage_id': stage_id,
                'stage_code': item['code'],
                'stage_name': item['name']
            }

    return stage_list


@singleton
class ArknightsGameData:
    def __init__(self):
        log.info('initialize ArknightsGameData...')

        self.stages = init_stages()
        self.enemies = init_enemies()
        self.operators, self.birthday = init_operators()
        self.materials, self.materials_map, self.materials_made, self.materials_source = init_materials()


class ArknightsGameDataResource:
    local_version_file = resource_config.save.data + '/version.txt'

    download_ignore_file = 'fileStorage/downloadFail.txt'
    download_ignore = []

    if os.path.exists(download_ignore_file):
        with open(download_ignore_file, mode='r', encoding='utf-8') as f:
            download_ignore = f.read().strip('\n').split('\n')

    @classmethod
    def __save_file(cls, url, save_path):
        if save_path in cls.download_ignore:
            return

        data = download_sync(url)
        if data:
            create_dir(save_path, is_file=True)
            with open(save_path, mode='wb+') as f:
                f.write(data)
        else:
            cls.download_ignore.append(save_path)

    @classmethod
    def refresh_download_ignore(cls):
        with open(cls.download_ignore_file, mode='w', encoding='utf-8') as f:
            f.write('\n'.join(cls.download_ignore))

    @classmethod
    def check_update(cls):
        log.info('checking ArknightsGameData update...')

        version = download_sync(f'{resource_config.remote.gameData.version}/gamedata/excel/data_version.txt',
                                stringify=True)

        if version is False:
            log.info(f'ArknightsGameData version file request failed.')
            return False

        local_ver = 'None'
        if os.path.exists(cls.local_version_file):
            with open(cls.local_version_file, mode='r') as v:
                local_ver = v.read().strip('\n')

        r = re.search(r'VersionControl:(.*)\n', version)
        if r:
            latest_ver = r.group(1)
            if latest_ver != local_ver:
                with open(cls.local_version_file, mode='w+') as v:
                    v.write(latest_ver)
                log.info(f'new ArknightsGameData version detected: latest {latest_ver} --> local {local_ver}')
                return True

            log.info(f'ArknightsGameData is up to date: {latest_ver}')
        else:
            log.info(f'ArknightsGameData update check failed.')

        return False

    @classmethod
    def download_data_fiels(cls, use_cache=False):
        if cls.check_update() is False:
            use_cache = True

        for name in log.progress_bar(resource_config.remote.gameData.files, 'ArknightsGameData'):
            url = f'{resource_config.remote.gameData.source}/gamedata/{name}'
            path = f'{resource_config.save.data}/' + name.split('/')[-1]

            if use_cache and os.path.exists(path):
                continue

            data = download_sync(url, stringify=True)
            if data:
                with open(path, mode='w+', encoding='utf-8') as src:
                    src.write(data)
            else:
                if os.path.exists(cls.local_version_file):
                    os.remove(cls.local_version_file)
                raise Exception(f'data [{name}] download failed')

    @classmethod
    def download_operators_resource(cls):
        operators = ArknightsGameData().operators
        remote = resource_config.remote.gameData.source

        resource = []

        for name, item in operators.items():
            skills_list = item.skills()[0]

            resource.append(f'{remote}/portrait/{item.id}_1.png')
            resource.append(f'{remote}/avatar/{item.id}.png')

            for skill in skills_list:
                resource.append(f'{remote}/skill/{skill["skill_icon"]}.png')

        for url in log.progress_bar(resource, 'operators resource'):
            save_path = 'resource/images/' + '/'.join(url.split('/')[-2:])

            if os.path.exists(save_path):
                continue

            cls.__save_file(url, save_path)

    @classmethod
    def download_materials_resource(cls):
        materials = ArknightsGameData().materials

        for m_id in log.progress_bar(materials, 'materials resource'):
            item = materials[m_id]

            url = f'{resource_config.remote.gameData.source}/item/%s.png' % item['material_icon']
            save_path = f'resource/images/item/%s.png' % item['material_icon']

            if os.path.exists(save_path):
                continue

            cls.__save_file(url, save_path)

    @classmethod
    def download_enemies_resource(cls):
        enemies = ArknightsGameData().enemies

        for name in log.progress_bar(enemies, 'enemies resource'):
            item = enemies[name]

            url = f'{resource_config.remote.gameData.source}/enemy/%s.png' % item['info']['enemyId']
            save_path = f'resource/images/enemy/%s.png' % item['info']['enemyId']

            if os.path.exists(save_path):
                continue

            cls.__save_file(url, save_path)
