import os
import re
import zipfile

from typing import List, Dict, Tuple
from core.network.download import download_sync, download_async
from core.resource import resource_config
from core.util import Singleton, remove_xml_tag, remove_punctuation, create_dir, sorted_dict, remove_dir
from core import log

from .common import ArknightsConfig, JsonData
from .operatorBuilder import Operator
from .wiki import Wiki

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

gamedata_path = 'resource/gamedata'


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

    for n, item in voice_data['charWords'].items():
        char_id = item['wordKey']

        if char_id not in voice_map:
            voice_map[char_id] = []

        voice_map[char_id].append(item)

    for n, item in skins_data.items():
        char_id = item['charId']
        skin_id = item['skinId']

        if 'char_1001_amiya2' in skin_id:
            char_id = 'char_1001_amiya2'

        if char_id not in skins_map:
            skins_map[char_id] = []

        skins_map[char_id].append(item)

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
    enemies_data = JsonData.get_json_data('enemy_database', folder='levels/enemydata')['enemies']

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


class ArknightsGameData(metaclass=Singleton):
    def __init__(self):
        log.info('initialize ArknightsGameData...')

        self.stages = init_stages()
        self.enemies = init_enemies()
        self.operators, self.birthday = init_operators()
        self.materials, self.materials_map, self.materials_made, self.materials_source = init_materials()


class ArknightsGameDataResource:
    create_dir('resource')

    local_version_file = 'resource/gamedata-lock.txt'

    @classmethod
    def check_gamedata_update(cls):
        log.info('checking ArknightsGameData update...')

        latest_ver: str = download_sync(f'{resource_config.remote.cos}/resource/gamedata/version.txt',
                                        stringify=True)

        if not latest_ver:
            log.error(f'ArknightsGameData version file request failed.')
            return None

        local_ver = 'None'
        if os.path.exists(cls.local_version_file):
            with open(cls.local_version_file, mode='r') as v:
                local_ver = v.read().strip('\n')

        if latest_ver != local_ver:
            log.info(f'new ArknightsGameData version detected: latest {latest_ver} --> local {local_ver}')
            return latest_ver

        else:
            log.info(f'ArknightsGameData is up to date: {latest_ver}')

        return None

    @classmethod
    def download_gamedata_files(cls):
        latest_ver = cls.check_gamedata_update()
        if not latest_ver:
            return None

        url = f'{resource_config.remote.cos}/resource/gamedata/Arknights-Bot-Resource-{latest_ver}.zip'
        path = f'resource/Arknights-Bot-Resource-{latest_ver}.zip'

        if not os.path.exists(path):
            data = download_sync(url, progress=True)
            if data:
                with open(path, mode='wb+') as src:
                    src.write(data)
                cls.unpack_gamedata_files(path)
            else:
                if os.path.exists(cls.local_version_file):
                    os.remove(cls.local_version_file)
                raise Exception(f'gamedata download failed')
        else:
            cls.unpack_gamedata_files(path)

        with open(cls.local_version_file, mode='w+') as v:
            v.write(latest_ver)

    @classmethod
    def unpack_gamedata_files(cls, path):
        log.info(f'unpacking {path}...')

        remove_dir(gamedata_path)
        create_dir(gamedata_path)

        pack = zipfile.ZipFile(path)
        for pack_file in pack.namelist():
            pack.extract(pack_file, gamedata_path)

    @classmethod
    async def get_skin_file(cls, operator: Operator, skin_data: dict):
        skin_file = f'{operator.id}_%s.png' % skin_data['skin_key']
        skin_path = f'resource/skins/{operator.id}/{skin_file}'

        if not os.path.exists(skin_path):
            log.error(f'can not found skin {skin_path}')
            return None
        return skin_path

    @classmethod
    async def get_voice_file(cls, operator: Operator, voice_key: str, cn: bool = False):
        file = await Wiki.check_exists(operator.wiki_name, voice_key, cn)
        if not file:
            file = await Wiki.download_operator_voices(operator.id, operator.wiki_name, voice_key, cn)
            if not file:
                return None
        return file
