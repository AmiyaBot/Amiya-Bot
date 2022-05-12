import os
import shutil
import zipfile

from core.network.download import download_sync
from core.resource import resource_config
from core.util import create_dir
from core import log


class BotResource:
    @classmethod
    def download_amiya_bot_console(cls):
        log.info('checking Amiya-Bot Console update...')

        version_file = download_sync(f'{resource_config.remote.cos}/console/version.txt', stringify=True)

        if not version_file:
            log.error('Amiya-Bot Console version file request failed.')
            return False

        version = version_file.strip('\n').split('\n').pop(0)

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
            return False

        create_dir('view')

        url = f'{resource_config.remote.cos}/console/{version}.zip'
        pack_zip = 'view/Amiya-Bot-console.zip'

        data = download_sync(url, progress=True)
        if data:
            with open(pack_zip, mode='wb+') as src:
                src.write(data)

            pack = zipfile.ZipFile(pack_zip)
            for pack_file in pack.namelist():
                pack.extract(pack_file, 'view')
        else:
            if os.path.exists(local_version_file):
                os.remove(local_version_file)
            raise Exception(f'console download failed')

        with open(local_version_file, mode='w+') as lv:
            lv.write(version)

    @classmethod
    def download_bot_resource(cls):
        create_dir('resource')

        url = f'{resource_config.remote.cos}/resource/assets/Amiya-Bot-assets.zip'
        version = f'{resource_config.remote.cos}/resource/assets/version.txt'
        lock_file = 'resource/assets-lock.txt'
        pack_zip = 'resource/Amiya-Bot-assets.zip'

        log.info('checking assets update...')

        flag = False
        latest_ver = download_sync(version, stringify=True)
        if os.path.exists(lock_file):
            if latest_ver:
                with open(lock_file, mode='r') as lf:
                    if lf.read() != latest_ver:
                        flag = True
        else:
            flag = True

        if flag:
            data = download_sync(url, progress=True)
            if data:
                with open(pack_zip, mode='wb+') as src:
                    src.write(data)

                pack = zipfile.ZipFile(pack_zip)
                for pack_file in pack.namelist():
                    pack.extract(pack_file, 'resource')
            else:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
                raise Exception(f'assets download failed')

        if latest_ver:
            with open(lock_file, mode='w+') as v:
                v.write(latest_ver)
        else:
            log.error('assets version file request failed.')
