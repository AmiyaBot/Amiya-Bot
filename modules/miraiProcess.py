import yaml
import psutil
import hashlib
import subprocess


class Process:
    def __init__(self, dir_path):
        self.exe_name = 'miraiOK.exe'
        self.dir_path = dir_path
        self.kill_process()

    def init_auto_login(self, user_id, passwords):
        with open(self.dir_path + '/config/Console/AutoLogin.yml', mode='w+') as file:
            m = hashlib.md5()
            m.update(bytes(passwords, encoding='utf-8'))

            login = {
                'plainPasswords': {
                    user_id: passwords
                }
            }

            yaml.dump(login, file)

    def start_process(self):
        subprocess.Popen('start ' + self.exe_name, cwd=self.dir_path, shell=True)

    def kill_process(self):
        for proc in psutil.process_iter():
            if proc.name() in [self.exe_name, 'java.exe']:
                proc.kill()

    def __del__(self):
        self.kill_process()
