from core.util.xmlReader import read_xml


class Config:
    conf = read_xml('configure/limitOperator.xml')

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

    limit = conf['limit'].split(',') + conf['linkage'].split(',')

    unavailable = []
    for name, item in conf['unavailable'].items():
        unavailable += item.split(',')
