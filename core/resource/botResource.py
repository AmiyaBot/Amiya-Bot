import os
import zipfile

from amiyabot.network.download import download_sync
from core.resource import remote_config
from core.util import create_dir
from core import log


def support_gbk(zip_file: zipfile.ZipFile):
    name_to_info = zip_file.NameToInfo
    for name, info in name_to_info.copy().items():
        real_name = name.encode('cp437').decode('gbk')
        if real_name != name:
            info.filename = real_name
            del name_to_info[name]
            name_to_info[real_name] = info
    return zip_file


class BotResource:
    @classmethod
    def download_bot_resource(cls):
        create_dir('resource')

        url = f'{remote_config.remote.cos}/resource/assets/Amiya-Bot-assets.zip'
        version = f'{remote_config.remote.cos}/resource/assets/version.txt'
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
                for pack_file in support_gbk(pack).namelist():
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
