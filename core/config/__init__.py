import os
import yaml

from attrdict import AttrDict
from .defaultVar import func_setting_default, func_setting_path


def read_yaml(path, _dict=False):
    with open(path, mode='r', encoding='utf-8') as f:
        content = yaml.safe_load(f)
        if not _dict:
            content = AttrDict(content)
    return content


def func_setting(_dict=False):
    return read_yaml(func_setting_path, _dict)


def check_func_setting():
    curr_setting = func_setting_default

    if os.path.exists(func_setting_path):
        curr_setting = func_setting(_dict=True)

        def check_key(curr, default):
            for key in default.keys():
                if key not in curr:
                    curr[key] = default[key]
                else:
                    if type(default[key]) is dict:
                        check_key(curr[key], default[key])
                    elif isinstance(curr[key], type(default[key])):
                        curr[key] = default[key]

        check_key(curr_setting, func_setting_default)

    with open(func_setting_path, mode='w+', encoding='utf-8') as file:
        file.write('# 谨慎修改本文件，请使用后台修改功能设置\n' + yaml.dump(curr_setting))


check_func_setting()
config = read_yaml('config.yaml')
keyword = read_yaml('configure/keyword.yaml')
reward = read_yaml('configure/reward.yaml')
nudge = read_yaml('configure/nudge.yaml').nudge
files = read_yaml('configure/botFiles.yaml').files
