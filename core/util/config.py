import json

from core.util.xmlReader import read_xml


def get(data, name: str = None):
    if name:
        for item in name.split('.'):
            if item in data:
                data = data[item]
            else:
                raise Exception('can not found key "%s" in "%s"' % (item, name))
    return data


def config(name: str = None):
    with open('config.json', mode='r', encoding='utf-8') as conf:
        return get(json.load(conf), name)


def keyword(name: str = None):
    return get(read_xml('configure/keyword.xml'), name)


def reward(name: str = None):
    return get(read_xml('configure/reward.xml'), name)


def files(name: str = None):
    return get(read_xml('configure/botFiles.xml'), name)


def nudge(name: str = None):
    return get(read_xml('configure/nudge.xml'), name)
