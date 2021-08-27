import re
import os
import json
import requests

from core.util import log
from core.util.config import files
from requests_html import HTMLSession, HTML


class SourceBank:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) '
                          'AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1'
        }

        self.bot_source = 'https://cdn.jsdelivr.net/gh/vivien8261/Amiya-Bot-resource@master'
        self.bot_paths = {
            'face': 'resource/images/face',
            'style': 'resource/style',
            'gacha': 'resource/images/gacha',
            'class': 'resource/images/class'
        }

        self.github_source = 'https://cdn.jsdelivr.net/gh/Kengxxiao/ArknightsGameData@master/zh_CN/gamedata'
        self.resource_path = 'resource/data'

        self.pics_source = 'https://andata.somedata.top/dataX'
        self.pics_source_wiki = 'http://prts.wiki'
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

        self.local_version_file = f'{self.resource_path}/version.txt'

        self.wiki_session = HTMLSession()

        for item in [self.resource_path, self.pics_path]:
            if os.path.exists(item) is False:
                os.makedirs(item)

    def request_file(self, url, stringify=True):
        try:
            stream = requests.get(url, headers=self.headers, stream=True)
            if stream.status_code == 200:
                if stringify:
                    return str(stream.content, encoding='utf-8')
                else:
                    return stream.content
        except Exception as e:
            log.error(repr(e))
        return False

    def request_file_from_wiki(self, name):
        try:
            url = f'{self.pics_source_wiki}/w/文件:{name}.png'
            html: HTML = self.wiki_session.get(url, headers=self.headers).html

            file = html.find('#file > a', first=True)
            furl = self.pics_source_wiki + file.attrs['href']
            return self.request_file(furl, stringify=False)
        except Exception as e:
            log.error(repr(e))
        return False

    def get_pic(self, name, _type, _param='', _wiki='', _index=''):

        if os.path.exists('ignore.json'):
            with open('ignore.json', mode='r', encoding='utf-8') as file:
                ignore = json.load(file)
                if 'image_download' not in ignore:
                    ignore['image_download'] = []
        else:
            ignore = {
                'image_download': []
            }

        url = f'{self.pics_source}/{name}.png{_param}'
        save_path = f'{self.pics_path}/{_type}'
        image_path = f'{save_path}/{name.split("/")[-1]}.png'

        if os.path.exists(save_path) is False:
            os.makedirs(save_path)

        if os.path.exists(image_path) is False and image_path not in ignore['image_download']:

            log.info(f'downloading image {_index or "_/_"} [{image_path}]...')

            pic = self.request_file_from_wiki(_wiki) if _wiki else self.request_file(url, stringify=False)
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

    def download_bot_resource(self):
        bot_file = files()
        for name, _list in bot_file.items():
            for item in _list:
                path = self.bot_paths[name]
                save = f'{path}/{item.split("/")[-1]}'
                url = f'{self.bot_source}/{item}'

                if os.path.exists(save) is False:
                    if os.path.exists(path) is False:
                        os.makedirs(path)

                    log.info(f'downloading file [{item}]...')

                    data = self.request_file(url, stringify=False)
                    if data:
                        with open(save, mode='wb+') as src:
                            src.write(data)
