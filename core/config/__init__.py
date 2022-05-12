from core import log
from core.util import read_yaml, create_yaml, combine_dict

from .mahConfig import MiraiApiHttp
from .adminConfig import Admin
from .baiduConfig import BaiduCloud
from .serverConfig import ServerConfig
from .covidConfig import CovidConfig
from .testConfig import TestConfig

config_file = 'config/config.yaml'


class Config:
    admin: Admin
    baiduCloud: BaiduCloud
    httpServer: ServerConfig
    miraiApiHttp: MiraiApiHttp
    covid: CovidConfig
    test: TestConfig

    @classmethod
    def desc(cls):
        return {
            'admin': Admin.desc(),
            'baiduCloud': BaiduCloud.desc(),
            'httpServer': ServerConfig.desc(),
            'miraiApiHttp': MiraiApiHttp.desc(),
            'covid': CovidConfig.desc(),
            'test': TestConfig.desc(),
        }


log.info('inspecting and loading Configuration...')

if not create_yaml(config_file, Config.desc()):
    combine = combine_dict(read_yaml(config_file, _dict=True), Config.desc())
    create_yaml(config_file, combine, overwrite=True)

log.info('Configuration loading completed.')

config: Config = read_yaml(config_file)

