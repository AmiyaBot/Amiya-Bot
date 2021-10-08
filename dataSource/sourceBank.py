import re
import os
import json
import shutil

from core.util import log
from core.util.config import files
from core.util.common import make_folder
from core.database.manager import exec_sql_file
from core.network.httpRequests import DownloadTools

from .wiki import Wiki


class SourceBank(DownloadTools):
    def __init__(self):
        self.bot_source = 'http://vivien8261.gitee.io/amiya-bot-resource'
        self.bot_console = 'http://vivien8261.gitee.io/amiya-bot-console'
        self.bot_paths = {
            'face': 'resource/images/face',
            'style': 'resource/style',
            'gacha': 'resource/images/gacha',
            'class': 'resource/images/class',
            'database': 'resource/database'
        }

        self.github_source = 'https://cdn.jsdelivr.net/gh/Kengxxiao/ArknightsGameData@master/zh_CN/gamedata'
        self.resource_path = 'resource/data'

        self.pics_source = {
            'gitee': f'{self.bot_source}/images/game',
            'cloud': f'http://49.232.166.115:18080/resource/images/game/skins'
        }
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
            'excel/range_table',
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

    def get_pic(self, name, _type, _source='gitee', _save_ignore=True):

        ignore = self.get_ignore()

        url = f'{self.pics_source[_source]}/{name}.png'
        save_path = f'{self.pics_path}/{_type}'
        image_path = f'{save_path}/{name.split("/")[-1]}.png'

        make_folder(save_path)

        if image_path in ignore['image_download']:
            return False

        if os.path.exists(image_path) is False:
            pic = self.request_file(url, stringify=False)
            if pic:
                with open(image_path, mode='wb+') as _pic:
                    _pic.write(pic)
                return True
            else:
                if _save_ignore:
                    ignore['image_download'].append(image_path)
                    self.save_ignore(ignore)
                return False
        else:
            return True

    def get_json_data(self, name):
        if name not in self.source_bank:
            with open(f'{self.resource_path}/{name}.json', mode='r', encoding='utf-8') as src:
                self.source_bank[name] = json.load(src)

        return self.source_bank[name]

    def check_update(self):
        log.info('checking Github update...')

        version = self.request_file(f'{self.github_source}/excel/data_version.txt')

        if version is False:
            log.info(f'Github version file request failed.')
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
                log.info(f'new Github version detected: latest {latest_ver} --> local {local_ver}')
                return True

            log.info(f'Github version is up to date: {latest_ver}')
        else:
            log.info(f'Github update check failed.')

        return False

    def download_resource(self, use_cache=False):

        if self.check_update() is False:
            use_cache = True

        for name, status in log.download_src(self.resource, 'gameData'):
            url = '%s/%s.json' % (self.github_source, name)
            path = '%s/%s.json' % (self.resource_path, name.split('/')[-1])

            if use_cache and os.path.exists(path):
                status.success()
                continue

            data = self.request_file(url)
            if data:
                with open(path, mode='w+', encoding='utf-8') as src:
                    src.write(data)
                    status.success()
            else:
                if os.path.exists(self.local_version_file):
                    os.remove(self.local_version_file)
                raise Exception(f'data [{name}] download failed')

    def download_bot_resource(self, refresh=False):
        for name, _list in files.items():
            if type(_list) is str:
                _list = [_list]

            for item, status in log.download_src(_list, name):
                path = self.bot_paths[name]
                save = f'{path}/{item.split("/")[-1]}'
                url = f'{self.bot_source}/{item}'

                if os.path.exists(save) is False or refresh:
                    make_folder(path)

                    data = self.request_file(url, stringify=False)
                    if data:
                        with open(save, mode='wb+') as src:
                            src.write(data)

                        if name == 'database' and not refresh:
                            exec_sql_file(file=save)
                    else:
                        raise Exception(f'file [{item}] download failed')

                status.success()

    def download_bot_console(self):
        log.info('checking Console update...')

        version_file = self.request_file(f'{self.bot_console}/.version')

        if not version_file:
            return False

        file_list = version_file.strip('\n').split('\n')
        version = file_list.pop(0)

        local_ver = None
        local_version_file = 'view/version.txt'
        need_update = False
        if os.path.exists(local_version_file) is False:
            need_update = True
        else:
            with open(local_version_file, mode='r') as lv:
                local_ver = lv.read()
                if version != local_ver:
                    need_update = True

        if need_update:
            log.info(f'new Console version detected: latest {version} --> local {local_ver}')
            if os.path.exists('view'):
                shutil.rmtree('view')
        else:
            log.info(f'Console version is up to date: {version}')

        make_folder('view')
        with open(local_version_file, mode='w+') as lv:
            lv.write(version)

        for file, status in log.download_src(file_list, 'console'):
            view_path = f'view/{file}'
            if not os.path.exists(view_path) or need_update:
                folder = '/'.join(view_path.split('/')[0:-1])
                suffix = view_path.split('.')[-1]

                make_folder(folder)

                text_file = suffix in ['html', 'css', 'js', 'map']
                url = f'{self.bot_console}/dist/{file}'

                data = self.request_file(url, stringify=text_file)
                if data:
                    with open(view_path,
                              mode='w+' if text_file else 'wb+',
                              encoding='utf-8' if text_file else None) as src:
                        src.write(data)
                        status.success()
                else:
                    log.error(f'file [{file}] download failed', stdout=False)
                    status.fail()
            else:
                status.success()

    @staticmethod
    def get_ignore(reset=False):
        if os.path.exists('ignore.json'):
            with open('ignore.json', mode='r', encoding='utf-8') as file:
                ignore = json.load(file)
                if 'image_download' not in ignore:
                    ignore['image_download'] = []
                if 'weibo_download' not in ignore:
                    ignore['weibo_download'] = []
        else:
            ignore = {
                'image_download': [],
                'weibo_download': []
            }

        if reset:
            ignore['image_download'] = []
            with open('ignore.json', mode='w+', encoding='utf-8') as file:
                file.write(json.dumps(ignore, ensure_ascii=False))

        return ignore

    @staticmethod
    def save_ignore(data):
        with open('ignore.json', mode='w+', encoding='utf-8') as file:
            file.write(json.dumps(data, ensure_ascii=False))
