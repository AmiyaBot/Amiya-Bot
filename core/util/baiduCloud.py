import requests

from core.util import log
from aip import AipNlp, AipOcr, AipContentCensor


class Options:
    enable: bool
    appId: int
    apiKey: str
    secretKey: str


class NaturalLanguage:
    def __init__(self, options: Options):
        if options.enable:
            self.client = AipNlp(str(options.appId), options.apiKey, options.secretKey)
            self.enable = True
        else:
            self.client = None
            self.enable = False

    def emotion(self, text):
        if self.enable is False:
            return False

        with log.except_error():
            result = self.client.emotion(text, {
                'scene': 'talk'
            })
            if 'error_code' in result:
                return False
            return result


class OpticalCharacterRecognition:
    def __init__(self, options: Options):
        if options.enable:
            self.client = AipOcr(str(options.appId), options.apiKey, options.secretKey)
            self.enable = True
        else:
            self.client = None
            self.enable = False

    def basic_general(self, image):
        if self.enable is False:
            return False

        with log.except_error():
            options = {
                'detect_direction': 'true'
            }
            result = self.client.basicGeneralUrl(image, options)
            return result

    def basic_accurate(self, image):
        if self.enable is False:
            return False

        with log.except_error():
            stream = requests.get(image, stream=True)
            if stream.status_code == 200:
                options = {
                    'detect_direction': 'true'
                }
                result = self.client.basicAccurate(stream.content, options)
                return result


class ContentCensor:
    def __init__(self, options: Options):
        if options.enable:
            self.client = AipContentCensor(str(options.appId), options.apiKey, options.secretKey)
            self.enable = True
        else:
            self.client = None
            self.enable = False

    def text_censor(self, text):
        if self.enable is False:
            return False

        with log.except_error():
            result = self.client.textCensorUserDefined(text)
            if 'error_code' in result:
                return False
            return result
