import json

from core.util import read_yaml
from core.resource import resource_config

config = read_yaml('config/private/arknights.yaml', _dict=True)['operatorSetting']


class ArknightsConfig:
    high_star = config['high_star']
    classes = config['classes']
    types = config['types']
    attr_dict = config['attr_dict']
    attr_lower_dict = {**config['attr_dict'], **config['attr_lower_dict']}

    limit = []
    unavailable = []


class JsonData:
    cache = {}

    @classmethod
    def get_json_data(cls, name):
        if name not in cls.cache:
            with open(f'{resource_config.save.data}/{name}.json', mode='r', encoding='utf-8') as src:
                cls.cache[name] = json.load(src)
        return cls.cache[name]
