import re
import os
import sys
import shutil
import zipfile
import pathlib
import logging

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
                        StringStruct(u'ProductName', u'AmiyaBot'),
                        StringStruct(u'ProductVersion', u'{file_version}'),
                        StringStruct(u'FileDescription', u'《明日方舟》QQ机器人'),
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


def upload_pack(folder, pack_name):
    from qcloud_cos import CosConfig
    from qcloud_cos import CosS3Client

    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    with open('baidu.txt', mode='r') as conf:
        conf = conf.read().strip().split('\n')
        secret_id = conf[0]
        secret_key = conf[1]

    config = CosConfig(
        Region='ap-guangzhou',
        SecretId=secret_id,
        SecretKey=secret_key
    )
    client = CosS3Client(config)

    bucket = client.list_buckets()['Buckets']['Bucket'][0]['Name']

    client.put_object_from_local_file(
        Bucket=bucket,
        LocalFilePath=f'{folder}/version.txt',
        Key='package/version5.txt',
    )
    client.put_object_from_local_file(
        Bucket=bucket,
        LocalFilePath=f'{folder}/{pack_name}',
        Key=f'package/{pack_name}',
    )


def build(version, folder):
    dist = f'{folder}/dist'
    local = '/'.join(sys.argv[0].replace('\\', '/').split('/')[:-1])

    if os.path.exists(dist):
        shutil.rmtree(dist)

    os.makedirs(dist)

    shutil.copy(f'{venv}/jieba/dict.txt', f'{dist}/dict.txt')
    shutil.copytree('config/private', f'{dist}/config/private', dirs_exist_ok=True)

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
        f'pyi-makespec -F -n AmiyaBot-{version} -i {local}/amiya.ico'
        f' --version-file={folder}/version.txt {local}/amiya.py',
        f'pyinstaller AmiyaBot-{version}.spec'
    ]

    msg = os.popen('&'.join(cmd)).readlines()

    for item in msg:
        print(item)

    pack_name = f'AmiyaBot-{version}.zip'
    path = pathlib.Path(f'{folder}/{pack_name}')

    with zipfile.ZipFile(path, 'w') as pack:
        for root, dirs, files in os.walk(dist):
            for index, filename in enumerate(files):
                target = os.path.join(root, filename)
                path = target.replace(dist + '\\', '')
                pack.write(target, path)

    with open(f'{folder}/version.txt', 'w+') as ver:
        ver.write(version)

    try:
        upload_pack(folder, pack_name)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    v = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != 'null' else input('version: ')
    f = sys.argv[2] if len(sys.argv) > 2 else '.'

    build(v, f)
