from dataclasses import dataclass, field
from core.util import init_config_file


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
    return init_config_file(file, RemoteConfig)


remote_config = init('config/remote.yaml')
