from core.util import read_yaml


class Remote:
    cos: str
    wiki: str


class ResourceConfig:
    remote: Remote


resource_config: ResourceConfig = read_yaml('config/private/cos.yaml')
