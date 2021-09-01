import re
import os
import json

from core.util import log
from core.util.config import files
from core.util.common import make_folder
from core.database.manager import exec_sql_file
from core.network.httpRequests import DownloadTools

from .wiki import Wiki


class SourceBank(DownloadTools):
    def __init__(self):
        self.bot_source = 'https://cdn.jsdelivr.net/gh/vivien8261/Amiya-Bot-resource@master'
        self.bot_console = 'https://cdn.jsdelivr.net/gh/vivien8261/Amiya-Bot-console@master'
        self.bot_paths = {
            'face': 'resource/images/face',
            'style': 'resource/style',
            'gacha': 'resource/images/gacha',
            'class': 'resource/images/class',
            'database': 'resource/database'
        }

        self.github_source = 'https://cdn.jsdelivr.net/gh/Kengxxiao/ArknightsGameData@master/zh_CN/gamedata'
        self.resource_path = 'resource/data'

        self.pics_source = 'https://andata.somedata.top/dataX'
        self.pics_path = 'resource/images'

        self.resource = [
            'levels/enemydata/enemy_database',
            'excel/enemy_handbook_table',
            'excel/handbook_info_table',
            'excel/battle_equip_table',
            'excel/char_patch_table',
            'excel/character_table',
            'excel/uniequip_table',
            'excel/charword_table',
            'excel/building_data',
            'excel/gacha_table',
            'excel/stage_table',
            'excel/skill_table',
            'excel/skin_table',
            'excel/item_table'
        ]
        self.source_bank = {}
        self.wiki = Wiki()

        self.local_version_file = f'{self.resource_path}/version.txt'

        for item in [self.resource_path, self.pics_path]:
            make_folder(item)

    def get_pic(self, name, _type, _param='', _wiki='', _index=''):

        ignore = self.reset_ignore()

        url = f'{self.pics_source}/{name}.png{_param}'
        save_path = f'{self.pics_path}/{_type}'
        image_path = f'{save_path}/{name.split("/")[-1]}.png'

        make_folder(save_path)

        if os.path.exists(image_path) is False and image_path not in ignore['image_download']:

            log.info(f'downloading image {_index or "_/_"} [{image_path}]...')

            pic = self.wiki.request_pic_from_wiki(_wiki) if _wiki else self.request_file(url, stringify=False)
            if pic:
                with open(image_path, mode='wb+') as _pic:
                    _pic.write(pic)
                return True
            else:
                ignore['image_download'].append(image_path)
                with open('ignore.json', mode='w+', encoding='utf-8') as file:
                    file.write(json.dumps(ignore, ensure_ascii=False))
        else:
            return True

    def get_json_data(self, name):
        if name not in self.source_bank:
            with open('%s/%s.json' % (self.resource_path, name), mode='r', encoding='utf-8') as src:
                self.source_bank[name] = json.load(src)

        return self.source_bank[name]

    def check_update(self):
        log.info('checking update...')

        version = self.request_file(f'{self.github_source}/excel/data_version.txt')

        if version is False:
            log.info(f'version file request failed.')
            return False

        local_ver = 'None'
        if os.path.exists(self.local_version_file):
            with open(self.local_version_file, mode='r') as v:
                local_ver = v.read().strip('\n')

        r = re.search(r'VersionControl:(.*)\n', version)
        if r:
            latest_ver = r.group(1)
            if latest_ver != local_ver:
                with open(self.local_version_file, mode='w+') as v:
                    v.write(latest_ver)
                log.info(f'new version detected: latest {latest_ver} --> local {local_ver}')
                return True

            log.info(f'version is up to date: {latest_ver}')
        else:
            log.info(f'update check failed.')

        return False

    def download_resource(self, use_cache=False):

        if self.check_update() is False:
            use_cache = True

        for name in self.resource:
            url = '%s/%s.json' % (self.github_source, name)
            path = '%s/%s.json' % (self.resource_path, name.split('/')[-1])

            if use_cache and os.path.exists(path):
                continue

            log.info(f'downloading data [{name}]...')
            data = self.request_file(url)
            if data:
                with open(path, mode='w+', encoding='utf-8') as src:
                    src.write(data)
            else:
                os.remove(self.local_version_file)
                raise Exception(f'data [{name}] download failed')

    def download_bot_resource(self, refresh=False):
        bot_file = files()
        for name, _list in bot_file.items():
            if type(_list) is str:
                _list = [_list]

            for item in _list:
                path = self.bot_paths[name]
                save = f'{path}/{item.split("/")[-1]}'
                url = f'{self.bot_source}/{item}'

                if os.path.exists(save) is False or refresh:
                    make_folder(path)

                    log.info(f'downloading file [{item}]...')

                    data = self.request_file(url, stringify=False)
                    if data:
                        with open(save, mode='wb+') as src:
                            src.write(data)

                        if name == 'database':
                            exec_sql_file(file=save)
                    else:
                        raise Exception(f'file [{item}] download failed')

    def download_bot_console(self):
        version = self.request_file(f'{self.bot_console}/.version').strip('\n').split('\n')
        for file in version:
            view_path = f'view/{file}'
            if not os.path.exists(view_path):
                folder = '/'.join(view_path.split('/')[0:-1])
                suffix = view_path.split('.')[-1]

                make_folder(folder)

                text_file = suffix in ['html', 'css', 'js', 'map']
                url = f'{self.bot_console}/dist/{file}'

                log.info(f'downloading file [{view_path}]...')

                data = self.request_file(url, stringify=text_file)
                if data:
                    with open(view_path,
                              mode='w+' if text_file else 'wb+',
                              encoding='utf-8' if text_file else None) as src:
                        src.write(data)
                else:
                    log.error(f'file [{file}] download failed')

    @staticmethod
    def reset_ignore(reset=False):
        if os.path.exists('ignore.json'):
            with open('ignore.json', mode='r', encoding='utf-8') as file:
                ignore = json.load(file)
                if 'image_download' not in ignore:
                    ignore['image_download'] = []
        else:
            ignore = {
                'image_download': []
            }

        if reset:
            ignore['image_download'] = []
            with open('ignore.json', mode='w+', encoding='utf-8') as file:
                file.write(json.dumps(ignore, ensure_ascii=False))

        return ignore
