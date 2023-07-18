from core.util import read_yaml


class Remote:
    cos: str
    wiki: str
    console: str
    penguin: str
    gamedata: str


class Bucket:
    enabled: bool
    region: str
    secret_id: str
    secret_key: str
    bucket_name: str


class RemoteConfig:
    remote: Remote
    bucket: Bucket


remote_config: RemoteConfig = read_yaml('config/remote.yaml')
