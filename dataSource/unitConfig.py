from core.database.models import GachaConfig


class Config:
    high_star = {
        '5': '资深干员',
        '6': '高级资深干员'
    }
    classes = {
        'PIONEER': '先锋',
        'WARRIOR': '近卫',
        'TANK': '重装',
        'SNIPER': '狙击',
        'CASTER': '术师',
        'SUPPORT': '辅助',
        'MEDIC': '医疗',
        'SPECIAL': '特种'
    }
    types = {
        'MELEE': '近战',
        'RANGED': '远程'
    }

    limit = []
    unavailable = []

    for item in GachaConfig.select():
        item: GachaConfig
        if item.operator_type in [0, 1]:
            limit.append(item.operator_name)
        else:
            unavailable.append(item.operator_name)
