import collections

from core.util import read_yaml
from core.util import create_dir


class GameData:
    version: str
    source: str
    files: list


class Remote:
    console: str
    resource: str
    gameData: GameData


class Save:
    data: str
    face: str
    style: str
    gacha: str
    classify: str
    database: str

    @classmethod
    def values(cls) -> collections.Iterable:
        pass


class ResourceConfig:
    remote: Remote
    save: Save


resource_config: ResourceConfig = read_yaml('config/resource.yaml')

for item in resource_config.save.values():
    create_dir(item)
