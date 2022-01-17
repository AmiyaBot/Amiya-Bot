from core import log
from core.util import read_yaml, create_yaml, combine_dict

from .mahConfig import MiraiApiHttp
from .adminConfig import Admin
from .ImageConfig import ImageCreator
from .databaseConfig import Databases
from .speedConfig import SpeedSetting
from .baiduConfig import BaiduCloud

config_file = 'config/config.yaml'


class Config:
    admin: Admin
    miraiApiHttp: MiraiApiHttp
    imageCreator: ImageCreator
    databases: Databases
    speedSetting: SpeedSetting
    baiduCloud: BaiduCloud

    @classmethod
    def desc(cls):
        return {
            'admin': Admin.desc(),
            'miraiApiHttp': MiraiApiHttp.desc(),
            'imageCreator': ImageCreator.desc(),
            'databases': Databases.desc(),
            'speedSetting': SpeedSetting.desc(),
            'baiduCloud': BaiduCloud.desc(),
        }


log.info('inspecting and loading Configuration...')

if not create_yaml(config_file, Config.desc()):
    combine = combine_dict(read_yaml(config_file, _dict=True), Config.desc())
    create_yaml(config_file, combine, overwrite=True)

log.info('Configuration loading completed.')

config: Config = read_yaml(config_file)
