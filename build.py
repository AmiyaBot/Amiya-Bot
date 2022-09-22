import re
import os
import sys
import shutil
import zipfile
import pathlib
import logging

from urllib import request, error
from jionlp.util.zip_file import ZIP_FILE_LIST

venv = 'venv/Lib/site-packages'
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
                        StringStruct(u'FileDescription', u'《明日方舟》QQ机器人，内置游戏资料查询，模拟抽卡，公招识别等多种功能'),
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
    (os.path.abspath(f'{venv}/amiyabot/assets'), 'amiyabot/assets'),
    (os.path.abspath(f'{venv}/amiyabot/network/httpServer'), 'amiyabot/network/httpServer')
]


def argv(name, formatter=str):
    key = f'--{name}'
    if key in sys.argv:
        index = sys.argv.index(key) + 1

        if index >= len(sys.argv):
            return True

        if sys.argv[index].startswith('--'):
            return True
        else:
            return formatter(sys.argv[index])


def build(version, folder, branch):
    dist = f'{folder}/dist'
    local = '/'.join(sys.argv[0].replace('\\', '/').split('/')[:-1]) or '.'

    setup_name = f'AmiyaBot-{version}'
    if branch:
        setup_name += '-' + branch.split('-')[-1]

    try:
        latest = str(
            request.urlopen('https://cos.amiyabot.com/package/release/latest.txt').read(),
            encoding='utf-8').strip('\n')
    except error.HTTPError:
        latest = ''

    if not version:
        with open('.github/latest.txt', mode='r', encoding='utf-8') as ver:
            version = ver.read().strip('\n')

    if latest == version:
        print('not new release.')
        return None

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
        f'set PLAYWRIGHT_BROWSERS_PATH=0',
        f'playwright install chromium',
        f'pyi-makespec -F -n {setup_name} -i {local}/amiya.ico'
        f' --version-file={folder}/version.txt {local}/amiya.py' +
        ''.join([' --add-data=%s;%s' % df for df in data_files]),
        f'pyinstaller {setup_name}.spec'
    ]

    msg = os.popen('&'.join(cmd)).readlines()

    for item in msg:
        print(item)

    pack_name = f'{setup_name}.zip'
    path = pathlib.Path(f'{folder}/{pack_name}')

    with zipfile.ZipFile(path, 'w') as pack:
        for root, dirs, files in os.walk(dist):
            for index, filename in enumerate(files):
                target = os.path.join(root, filename)
                pack.write(target, target.replace(dist + '\\', ''))

    os.remove(f'{folder}/version.txt')

    upload_pack('.github/latest.txt', path, pack_name)


def upload_pack(ver_file, package_file, package_name):
    from qcloud_cos import CosConfig
    from qcloud_cos import CosS3Client

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

    client.put_object_from_local_file(
        Bucket=bucket,
        LocalFilePath=ver_file,
        Key='package/release/latest.txt',
    )
    client.put_object_from_local_file(
        Bucket=bucket,
        LocalFilePath=package_file,
        Key=f'package/release/{package_name}',
    )


if __name__ == '__main__':
    build(
        argv('version'),
        argv('folder') or '.',
        argv('branch')
    )
