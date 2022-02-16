from typing import Union
from aip import AipNlp, AipOcr, AipContentCensor
from core.network.download import download_async
from core.config import config
from core.util import run_in_thread_pool, Singleton
from core import log

conf = config.baiduCloud


class BaiduCloud(metaclass=Singleton):
    def __init__(self):
        self.enable = False
        self.__nlp = None
        self.__ocr = None
        self.__cc = None

        if conf.enable:
            options = (str(conf.appId), conf.apiKey, conf.secretKey)

            self.__nlp = AipNlp(*options)
            self.__ocr = AipOcr(*options)
            self.__cc = AipContentCensor(*options)

            self.enable = True

    async def emotion(self, text) -> Union[bool, dict]:
        """
        对话情绪识别接口
        """
        if not self.enable:
            return False

        async with log.catch():
            options = {
                'scene': 'talk'
            }
            result = await run_in_thread_pool(self.__nlp.emotion, text, options)
            if 'error_code' in result:
                return False
            return result

    async def web_image_url(self, url) -> Union[bool, dict]:
        """
        网络图片文字识别
        """
        if not self.enable:
            return False

        async with log.catch():
            options = {
                'detect_direction': 'true'
            }
            result = await run_in_thread_pool(self.__ocr.webImageUrl, url, options)
            return result

    async def basic_general(self, image: Union[str, bytes]) -> Union[bool, dict]:
        """
        通用文字识别
        """
        if not self.enable:
            return False

        async with log.catch():
            options = {
                'detect_direction': 'true'
            }
            result = await run_in_thread_pool(
                self.__ocr.basicGeneralUrl if type(image) is str else self.__ocr.basicGeneral,
                image,
                options
            )
            return result

    async def basic_accurate(self, image: Union[str, bytes]) -> Union[bool, dict]:
        """
        通用文字识别（高精度版）
        """
        if not self.enable:
            return False

        async with log.catch():
            stream = await download_async(image) if type(image) is str else image
            if stream:
                options = {
                    'detect_direction': 'true'
                }
                result = await run_in_thread_pool(self.__ocr.basicAccurate, stream, options)
                return result

    async def text_censor(self, text) -> Union[bool, dict]:
        """
        文本内容审核
        """
        if not self.enable:
            return False

        async with log.catch():
            result = await run_in_thread_pool(self.__cc.textCensorUserDefined, text)
            if 'error_code' in result:
                return False
            return result
