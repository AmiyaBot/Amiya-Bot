import os
import shutil
import zipfile
import pathlib
import sys
folder = '.'
venv = 'venv/Lib/site-packages'


def build(version):
    dist = f'{folder}/dist'

    if os.path.exists(dist):
        shutil.rmtree(dist)

    os.makedirs(dist)

    shutil.copy(f'{venv}/jieba/dict.txt', f'{dist}/dict.txt')
    shutil.copy(f'{venv}/requests/cacert.pem', f'{dist}/cacert.pem')

    shutil.copy('config.yaml', f'{dist}/config.yaml')
    shutil.copytree('configure', f'{dist}/configure', dirs_exist_ok=True)

    cmd = [f'cd {folder}']

    disc = folder.split(':')
    if len(disc) > 1:
        cmd.append(disc[0] + ':')

    cmd.append(f'pyinstaller -F -i {os.getcwd()}\\amiya.ico {os.getcwd()}\\amiya.py')
    msg = os.popen('&'.join(cmd)).readlines()

    for item in msg:
        print(item)

    exe = f'{dist}/AmiyaBot-{version}.exe'

    if os.path.exists(exe):
        os.remove(exe)
        os.rename(f'{dist}/amiya.exe', exe)

    path:pathlib.Path = pathlib.Path(f'{folder}/AmiyaBot-{version}.zip')
    with zipfile.ZipFile(path, 'w') as pack:
        for root, dirs, files in os.walk(dist):
            for index, filename in enumerate(files):
                target = os.path.join(root, filename)
                path = target.replace(dist + '\\', '')
                pack.write(target, path)
    with open(f'{folder}/.version', 'w+') as ver:
        ver.write(version)


if __name__ == '__main__':
    # 不知道为什么，action上用管道传入tag name文件名会有乱码，从sys.argv拿不会
    build(sys.argv[1])
