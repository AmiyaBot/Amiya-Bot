import re
import os
import sys
import jieba
import zipfile
import subprocess

from core.resource.botResource import resource_config
from core.network.download import download_sync
from core import log

bucket = resource_config.remote.cos


def check_upgrade():
    log.info('checking upgrade...')

    local_exe = sys.argv[0].replace('\\', '/').split('/')[-1]

    new_version = download_sync(f'{bucket}/package/version5.txt', stringify=True)
    if not new_version:
        log.info('upgrade check fail.')
        return False

    new_version = new_version.strip('\n')

    exe_name = f'AmiyaBot-{new_version}.exe'
    new_pack = f'AmiyaBot-{new_version}.zip'

    if exe_name == local_exe:
        log.info('AmiyaBot version is up to date.')
        return False

    log.info(f'difference detected, downloading new pack {new_pack}')

    pack = download_sync(f'{bucket}/package/{new_pack}', progress=True)
    if pack:
        with open(new_pack, mode='wb+') as f:
            f.write(pack)
        pack = zipfile.ZipFile(new_pack)
        for pack_file in pack.namelist():
            if os.path.exists(pack_file) is False:
                pack.extract(pack_file)
    else:
        log.info(f'new version download fail.')
        return False

    log.info(f'restart new pack in 3 sec...')

    cmd = f'''
            @echo off
            if not exist {exe_name} exit
            TIMEOUT /T 3 /NOBREAK
            del {os.path.realpath(sys.argv[0])}
            start {exe_name}
        '''

    with open('upgrade.bat', mode='w+') as file:
        file.write(
            re.compile(r'\n\s+').sub('\n', cmd).strip('\n')
        )
    subprocess.Popen('upgrade.bat')
    sys.exit()


def check_frozen():
    if hasattr(sys, 'frozen'):
        jieba.set_dictionary('./dict.txt')
        check_upgrade()


check_frozen()
