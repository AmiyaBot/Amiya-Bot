import os
import json
import requests


class SourceBank:
    def __init__(self, network=True):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) '
                          'AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1'
        }
        self.sql_source = 'https://cdn.jsdelivr.net/gh/vivien8261/Amiya-Bot-resource@master/Database/Data'
        self.sql_path = 'resource/data/sql'
        self.github_source = 'https://cdn.jsdelivr.net/gh/Kengxxiao/ArknightsGameData@master/zh_CN/gamedata'
        self.resource_path = 'resource/data'
        self.pics_source = 'https://andata.somedata.top/dataX'
        self.pics_path = 'resource/images'
        self.resource = [
            'levels/enemydata/enemy_database',
            'excel/enemy_handbook_table',
            'excel/handbook_info_table',
            'excel/character_table',
            'excel/char_meta_table',
            'excel/charword_table',
            'excel/building_data',
            'excel/gacha_table',
            'excel/stage_table',
            'excel/skill_table',
            'excel/skin_table',
            'excel/item_table'
        ]
        self.sql_files = [
            't_config_amiya',
            't_operator_gacha_config',
            't_pool'
        ]

        self.network = network

    def get_pic(self, name, _type, _param=''):
        if self.network:
            url = '%s/%s.png%s' % (self.pics_source, name, _param)
            path = '%s/%s/%s.png' % (self.pics_path, _type, name.split('/')[-1])
            if os.path.exists(path) is False:
                stream = requests.get(url, headers=self.headers, stream=True)
                if stream.status_code == 200:
                    with open(path, mode='wb') as _pic:
                        _pic.write(stream.content)
                    return True
            else:
                return True
        return False

    def get_json_data(self, name):
        path = '%s/%s.json' % (self.resource_path, name)
        with open(path, mode='r', encoding='utf-8') as src:
            return json.load(src)

    def request_json_data(self, url):
        stream = requests.get(url, headers=self.headers, stream=True)
        if stream.status_code == 200:
            content = json.loads(stream.content)
            return content
        return False

    def download_resource(self, use_cache):
        print('检查JSON资源...')
        for name in self.resource:
            url = '%s/%s.json' % (self.github_source, name)
            path = '%s/%s.json' % (self.resource_path, name.split('/')[-1])

            if os.path.exists(path) is False or not use_cache:
                print('下载资源 [%s]...' % name, end='')
                data = self.request_json_data(url)
                if data:
                    with open(path, mode='w+', encoding='utf-8') as src:
                        src.write(json.dumps(data, ensure_ascii=False))
                    print('成功')
                else:
                    print('失败')
            else:
                print('资源已存在 [%s]' % name)

    def download_sql_file(self, use_cache):
        print('检查SQL资源...')
        for name in self.sql_files:
            url = '%s/%s.sql' % (self.sql_source, name)
            path = '%s/%s.sql' % (self.sql_path, name)

            if os.path.exists(path) is False or not use_cache:
                print('下载资源 [%s]...' % name, end='')
                stream = requests.get(url, headers=self.headers, stream=True)
                if stream.status_code == 200:
                    data = str(stream.content, encoding='utf-8')
                    with open(path, mode='w+', encoding='utf-8') as src:
                        src.write(data)
                    print('成功')
                else:
                    print('失败')
            else:
                print('资源已存在 [%s]' % name)
