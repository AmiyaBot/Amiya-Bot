import json


def get_config(name: str = None):
    with open('config.json', mode='r', encoding='utf-8') as conf:
        config = json.load(conf)

    if name:
        for item in name.split('.'):
            if item in config:
                config = config[item]
            else:
                raise Exception('can not found config key "%s" in "%s"' % (item, name))

    return config
