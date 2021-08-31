import requests
import traceback

from core.util import log
from aip import AipNlp, AipOcr


class NaturalLanguage:
    def __init__(self, options):
        if options['enable']:
            self.client = AipNlp(options['appId'], options['apiKey'], options['secretKey'])
            self.enable = True
        else:
            self.client = None
            self.enable = False

    def emotion(self, text):
        if self.enable is False:
            return False
        try:
            result = self.client.emotion(text, {
                'scene': 'talk'
            })
            if 'error_code' in result:
                print(result['error_msg'])
                return False
            return result
        except UnicodeEncodeError:
            return False


class OpticalCharacterRecognition:
    def __init__(self, options):
        if options['enable']:
            self.client = AipOcr(options['appId'], options['apiKey'], options['secretKey'])
            self.enable = True
        else:
            self.client = None
            self.enable = False

    def basic_general(self, image):
        if self.enable is False:
            return False
        options = {
            'detect_direction': 'true'
        }
        result = self.client.basicGeneralUrl(image, options)
        return result

    def basic_accurate(self, image):
        if self.enable is False:
            return False

        # noinspection PyBroadException
        try:
            stream = requests.get(image, stream=True)
            if stream.status_code == 200:
                options = {
                    'detect_direction': 'true'
                }
                result = self.client.basicAccurate(stream.content, options)
                return result
        except Exception:
            log.error(traceback.format_exc())
            return False
