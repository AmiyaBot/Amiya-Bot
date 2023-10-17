from .common import *
from .threadPool import *
from .timeRecorder import *
from .yamlManager import *
from .zipTools import *

jieba.setLogLevel(jieba.logging.INFO)


class Singleton(type):
    instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.instances:
            cls.instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instances[cls]


read_yaml = YamlManager.read_yaml
create_yaml = YamlManager.create_yaml
