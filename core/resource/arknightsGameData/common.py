import json

from core.database.bot import GachaConfig
from core.util import read_yaml

config = read_yaml('config/private/arknights.yaml', _dict=True)['operatorSetting']


class ArknightsConfig:
    high_star = config['high_star']
    classes = config['classes']
    types = config['types']
    attr_dict = config['attr_dict']
    attr_lower_dict = {**config['attr_dict'], **config['attr_lower_dict']}

    limit = []
    unavailable = []

    for item in GachaConfig.select():
        item: GachaConfig
        if item.operator_type in [0, 1]:
            limit.append(item.operator_name)
        else:
            unavailable.append(item.operator_name)


class JsonData:
    cache = {}

    @classmethod
    def get_json_data(cls, name, folder='excel'):
        if name not in cls.cache:
            with open(f'resource/gamedata/gamedata/{folder}/{name}.json',
                      mode='r',
                      encoding='utf-8') as src:
                cls.cache[name] = json.load(src)
        return cls.cache[name]
