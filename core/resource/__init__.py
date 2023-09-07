from core.util import read_yaml


class Remote:
    cos: str
    console: str
    resource: str


class RemoteConfig:
    remote: Remote


remote_config: RemoteConfig = read_yaml('config/remote.yaml')
