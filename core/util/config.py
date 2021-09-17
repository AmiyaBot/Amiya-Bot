import yaml

from attrdict import AttrDict


def read_yaml(path):
    with open(path, mode='r', encoding='utf-8') as f:
        content = AttrDict(yaml.safe_load(f))
    return content


def func_setting():
    return read_yaml('configure/functionSetting.yaml')


config = read_yaml('config.yaml')
keyword = read_yaml('configure/keyword.yaml')
reward = read_yaml('configure/reward.yaml')
nudge = read_yaml('configure/nudge.yaml').nudge
files = read_yaml('configure/botFiles.yaml').files
