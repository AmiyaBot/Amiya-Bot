import re
import os
import sys
import jieba
import zipfile
import subprocess

from core.network.httpRequests import DownloadTools
from core.util import log

server = 'http://49.232.166.115:18080/resource/dist'


def check_upgrade():
    log.info('checking upgrade...')

    local_exe = sys.argv[0].replace('\\', '/').split('/')[-1]

    new_version = DownloadTools.request_file(f'{server}/.version')
    if not new_version:
        log.info('upgrade check fail.')
        return False

    new_version = new_version.strip('\n')

    exe_name = f'AmiyaBot-{new_version}.exe'
    new_pack = f'AmiyaBot-{new_version}.zip'

    if exe_name == local_exe:
        return False

    log.info(f'difference detected, downloading new version {new_version}')

    pack = DownloadTools.request_file(f'{server}/{new_pack}', stringify=False)
    if pack:
        with open(new_pack, mode='wb+') as f:
            f.write(pack)
        pack = zipfile.ZipFile(new_pack)
        pack.extract(exe_name)
    else:
        log.info(f'new version download fail.')
        return False

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


if hasattr(sys, 'frozen'):
    jieba.set_dictionary('./dict.txt')
    os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(os.path.dirname(sys.argv[0]), 'cacert.pem')
    check_upgrade()
