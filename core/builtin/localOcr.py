"""
    Copyright 2022 AmiyaBot

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import aiofiles.os

from core.util import Singleton

try:
    from paddleocr import paddleocr
    from paddleocr import PaddleOCR

    paddleocr.logging.disable()
    enabled = True
except ModuleNotFoundError:
    enabled = False


class LocalOCR(metaclass=Singleton):
    def __init__(self):
        if enabled:
            self.__ocr = PaddleOCR(lang='ch')

    async def ocr(self, path: str):
        if not enabled:
            return ''

        result = [text[1][0] for text in self.__ocr.ocr(path)]
        await aiofiles.os.remove('tmp.jpg')
        return result
