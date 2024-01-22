from dataclasses import dataclass
from core.util import init_config_file


@dataclass
class CosConfig:
    activate: bool = False
    secret_id: str = ''
    secret_key: str = ''
    domain: str = ''
    folder: str = ''


def init(file: str) -> CosConfig:
    return init_config_file(file, CosConfig)


cos_config = init('config/cos.yaml')
