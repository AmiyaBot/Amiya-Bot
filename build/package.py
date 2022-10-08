import re
import os
import sys
import shutil
import zipfile
import pathlib
import logging
import subprocess

from urllib import request
from jionlp.util.zip_file import ZIP_FILE_LIST

venv = 'venv\\Lib\\site-packages'
scripts = 'venv\\Scripts'
if sys.platform == 'darwin':
    venv = 'venv\\lib\\python3.8\\site-packages'
    scripts = 'venv\\bin'

version_file = '''# UTF-8
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=({file_ver}, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x4,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    u'040904B0',
                    [
                        StringStruct(u'CompanyName', u'AmiyaBot'),
                        StringStruct(u'ProductName', u'《明日方舟》QQ机器人'),
                        StringStruct(u'ProductVersion', u'{file_version}'),
                        StringStruct(u'FileDescription', u'《明日方舟》QQ机器人，https://www.amiyabot.com'),
                        StringStruct(u'FileVersion', u'{file_version}'),
                        StringStruct(u'OriginalFilename', u'AmiyaBot.exe'),
                        StringStruct(u'LegalCopyright', u'Github AmiyaBot 组织版权所有'),
                    ]
                )
            ]
        ),
        VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
    ]
)
'''
data_files = [
    (os.path.abspath(f'{venv}/amiyabot/_assets').replace(' ', '\\ '), 'amiyabot/_assets'),
]


def build(version, folder, branch, force, upload=False):
    dist = f'{folder}/dist'
    local = os.path.abspath('/'.join(sys.argv[0].replace('\\', '/').split('/')[:-1]) or '.')

    try:
        cos_url = f'https://cos.amiyabot.com/package/release/latest-{branch}.txt'
        latest = str(
            request.urlopen(cos_url).read(),
            encoding='utf-8').strip('\r\n')
    except Exception:
        latest = ''

    if not version:
        with open('.github/latest.txt', mode='r', encoding='utf-8') as ver:
            version = ver.read().strip('\r\n')

    if latest == version and not force:
        print('not new release.')
        return None

    setup_name = f'AmiyaBot-{version}'
    if branch:
        setup_name += '-' + branch.split('-')[-1]

    if os.path.exists(dist):
        shutil.rmtree(dist)

    os.makedirs(dist)

    shutil.copy(f'{venv}/jieba/dict.txt', f'{dist}/dict.txt')
    shutil.copytree('config', f'{dist}/config', dirs_exist_ok=True)

    for item in ZIP_FILE_LIST:
        if not os.path.exists(f'{dist}/dictionary'):
            os.makedirs(f'{dist}/dictionary')
        print(f'moving {venv}/jionlp/dictionary/{item}')
        shutil.copy(f'{venv}/jionlp/dictionary/{item}', f'{dist}/dictionary/{item}')

    with open(f'{folder}/version.txt', mode='w+', encoding='utf-8') as vf:
        vf.write(
            version_file.format(
                file_ver=', '.join(re.findall(r'v(\d+).(\d+).(\d+)', version)[0]),
                file_version=version
            )
        )

    cmd = [
        f'cd {folder}'
    ]

    disc = folder.split(':')
    if len(disc) > 1:
        cmd.append(disc[0] + ':')

    cmd += [
        f'pyi-makespec -F -n {setup_name} -i {local}/amiya.ico'
        f' --version-file=version.txt {local}/amiya.py' +
        ''.join([' --add-data=%s;%s' % df for df in data_files]),
        f'set PLAYWRIGHT_BROWSERS_PATH=0',
        f'{os.path.abspath(scripts)}\\playwright install chromium',
        f'{os.path.abspath(scripts)}\\pyinstaller {setup_name}.spec'
    ]

    for cm in cmd:
        print('execute:', cm)

    build_process = subprocess.Popen('&'.join(cmd), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    for line in build_process.stdout.readlines():
        print(str(line, encoding='utf-8').strip('\r\n'))

    if not os.path.exists(f'{dist}/{setup_name}.exe'):
        print(f'no built {dist}/{setup_name}.exe.')
        return None

    pack_name = f'{setup_name}.zip'
    path = pathlib.Path(f'{folder}/{pack_name}')

    with zipfile.ZipFile(path, 'w') as pack:
        for root, dirs, files in os.walk(dist):
            for index, filename in enumerate(files):
                target = os.path.join(root, filename)
                pack.write(target, target.replace(dist + '\\', ''))

    os.remove(f'{folder}/version.txt')

    if upload:
        upload_pack('.github/latest.txt', branch, path, pack_name)


def upload_pack(ver_file, branch, package_file, package_name):
    from qcloud_cos import CosConfig, CosS3Client, CosClientError, CosServiceError

    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    secret_id = os.environ.get('SECRETID')
    secret_key = os.environ.get('SECRETKEY')

    config = CosConfig(
        Region='ap-guangzhou',
        SecretId=secret_id,
        SecretKey=secret_key
    )
    client = CosS3Client(config)

    bucket = client.list_buckets()['Buckets']['Bucket'][0]['Name']

    for i in range(0, 10):
        try:
            client.upload_file(
                Bucket=bucket,
                LocalFilePath=package_file,
                Key=f'package/release/{package_name}',
            )
            break
        except CosClientError or CosServiceError as e:
            print(e)

    client.put_object_from_local_file(
        Bucket=bucket,
        LocalFilePath=ver_file,
        Key=f'package/release/latest-{branch}.txt',
    )
