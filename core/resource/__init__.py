import collections

from typing import Union
from core.util import create_dir
from core.util import read_yaml


class GameData:
    version: str
    source: str
    files: list


class Remote:
    cos: str
    wiki: str
    gameData: GameData


class Files:
    data: Union[str, list]
    face: Union[str, list]
    rank: Union[str, list]
    style: Union[str, list]
    gacha: Union[str, list]
    classify: Union[str, list]
    database: Union[str, list]
    certificate: Union[str, list]

    @classmethod
    def items(cls):
        pass

    @classmethod
    def values(cls) -> collections.Iterable:
        pass


class ResourceConfig:
    remote: Remote
    save: Files
    files: Files


resource_config: ResourceConfig = read_yaml('config/private/resource.yaml')

for item in resource_config.save.values():
    create_dir(item)
