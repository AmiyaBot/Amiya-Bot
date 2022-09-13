import os
import json

from core.database.bot import OperatorConfig
from core.util import read_yaml

config = read_yaml('config/arknights.yaml', _dict=True)['operatorSetting']


class ArknightsConfig:
    classes = config['classes']
    token_classes = config['token_classes']
    high_star = config['high_star']
    types = config['types']

    limit = []
    unavailable = []

    @classmethod
    def initialize(cls):
        limit = []
        unavailable = []
        for item in OperatorConfig.select():
            item: OperatorConfig
            if item.operator_type in [0, 1]:
                limit.append(item.operator_name)
            else:
                unavailable.append(item.operator_name)

        cls.limit = limit
        cls.unavailable = unavailable


class JsonData:
    cache = {}

    @classmethod
    def get_json_data(cls, name, folder='excel'):
        if name not in cls.cache:
            path = f'resource/gamedata/gamedata/{folder}/{name}.json'
            if os.path.exists(path):
                with open(path, mode='r', encoding='utf-8') as src:
                    cls.cache[name] = json.load(src)
            else:
                return {}

        return cls.cache[name]
