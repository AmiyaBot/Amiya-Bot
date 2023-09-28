import os

from dataclasses import dataclass, asdict, field
from core.util import read_yaml, create_yaml, merge_dict


@dataclass
class Remote:
    cos: str = 'https://cos.amiyabot.com'
    plugin: str = 'https://server.amiyabot.com:8020'
    console: str = 'http://106.52.139.57:8000'
    resource: str = 'https://server.amiyabot.com:8000'


@dataclass
class RemoteConfig:
    remote: Remote = field(default_factory=Remote)


def init(file: str) -> RemoteConfig:
    config = {}
    if os.path.exists(file):
        config = read_yaml(file, _dict=True)

    create_yaml(file, merge_dict(config, asdict(RemoteConfig())), True)
    return read_yaml(file)


remote_config = init('config/remote.yaml')
