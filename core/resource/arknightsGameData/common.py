import os
import json

from core.database.bot import OperatorConfig

config = {
    'classes': {
        'CASTER': '术师',
        'MEDIC': '医疗',
        'PIONEER': '先锋',
        'SNIPER': '狙击',
        'SPECIAL': '特种',
        'SUPPORT': '辅助',
        'TANK': '重装',
        'WARRIOR': '近卫'
    },
    'token_classes': {
        'TOKEN': '召唤物',
        'TRAP': '装置'
    },
    'high_star': {
        '5': '资深干员',
        '6': '高级资深干员'
    },
    'types': {
        'ALL': '不限部署位',
        'MELEE': '近战位',
        'RANGED': '远程位'
    }
}

html_symbol = {
    '<替身>': '&lt;替身&gt;',
    '<支援装置>': '&lt;支援装置&gt;'
}


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
    def get_json_data(cls, name: str, folder: str = 'excel'):
        if name not in cls.cache:
            path = f'resource/gamedata/gamedata/{folder}/{name}.json'
            if os.path.exists(path):
                with open(path, mode='r', encoding='utf-8') as src:
                    cls.cache[name] = json.load(src)
            else:
                return {}

        return cls.cache[name]

    @classmethod
    def clear_cache(cls, name: str = None):
        if name:
            del cls.cache[name]
        else:
            cls.cache = {}
