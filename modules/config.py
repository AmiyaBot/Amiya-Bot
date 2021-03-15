import json


def get_config(name=None):
    with open('config.json', mode='r', encoding='utf-8') as conf:
        config = json.load(conf)

    if name is not None and name in config:
        return config[name]

    return config
