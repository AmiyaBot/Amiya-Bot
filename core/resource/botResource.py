import os
import shutil

from core.network.download import download_sync
from core.resource import resource_config
from core.util import create_dir
from core import log


class BotResource:
    @classmethod
    def download_amiya_bot_console(cls):
        log.info('checking Amiya-Bot Console update...')

        version_file = download_sync(f'{resource_config.remote.cos}/console/.version', stringify=True)

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
            log.info(f'new Amiya-Bot Console version detected: latest {version} --> local {local_ver}')
            if os.path.exists('view'):
                shutil.rmtree('view')
        else:
            log.info(f'Amiya-Bot Console is up to date: {version}')

        create_dir('view')

        with open(local_version_file, mode='w+') as lv:
            lv.write(version)

        for file in log.progress_bar(file_list, 'Amiya-Bot Console'):
            view_path = f'view/{file}'
            if not os.path.exists(view_path) or need_update:
                folder = '/'.join(view_path.split('/')[0:-1])
                suffix = view_path.split('.')[-1]

                create_dir(folder)

                text_file = suffix in ['html', 'css', 'js', 'map']
                url = f'{resource_config.remote.cos}/console/{version}/{file}'

                data = download_sync(url, stringify=text_file)
                if data:
                    with open(view_path,
                              mode='w+' if text_file else 'wb+',
                              encoding='utf-8' if text_file else None) as src:
                        src.write(data)
                else:
                    raise Exception(f'file [{file}] download failed.')

    @classmethod
    def download_bot_resource(cls, refresh=False):
        for name, items in resource_config.files.items():
            if not items:
                continue

            if type(items) is str:
                items = [items]

            for item in log.progress_bar(items, f'{name} resource'):
                path = getattr(resource_config.save, name)
                url = f'{resource_config.remote.cos}/resource/{item}'
                save = f'{path}/' + item.split('/')[-1]

                if os.path.exists(save) is False or refresh:
                    create_dir(path)

                    data = download_sync(url)
                    if data:
                        with open(save, mode='wb+') as src:
                            src.write(data)
                    else:
                        raise Exception(f'file [{item}] download failed')
