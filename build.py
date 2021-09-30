import os
import shutil

venv = 'venv/Lib/site-packages'
version = '4.0.1'


def build():
    shutil.copy(f'{venv}/jieba/dict.txt', 'dist/dict.txt')
    shutil.copy(f'{venv}/requests/cacert.pem', 'dist/cacert.pem')

    shutil.copy('config.yaml', 'dist/config.yaml')
    shutil.copytree('configure', 'dist/configure', dirs_exist_ok=True)

    for line in os.popen('pyinstaller -F -i amiya.ico amiya.py').readlines():
        print(line)

    exe = f'dist/AmiyaBot-{version}.exe'

    if os.path.exists(exe):
        os.remove(exe)
    os.rename('dist/amiya.exe', exe)

    shutil.rmtree('build')
    os.remove('amiya.spec')


if __name__ == '__main__':
    build()
