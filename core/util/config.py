import yaml

from attrdict import AttrDict

with open('config.yaml', mode='r', encoding='utf-8') as f:
    config = AttrDict(yaml.safe_load(f))

with open('configure/keyword.yaml', mode='r', encoding='utf-8') as f:
    keyword = AttrDict(yaml.safe_load(f))

with open('configure/nudge.yaml', mode='r', encoding='utf-8') as f:
    nudge = AttrDict(yaml.safe_load(f))

with open('configure/reward.yaml', mode='r', encoding='utf-8') as f:
    reward = AttrDict(yaml.safe_load(f))

with open('configure/botFiles.yaml', mode='r', encoding='utf-8') as f:
    files = AttrDict(yaml.safe_load(f))

