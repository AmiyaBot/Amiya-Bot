import os
import asyncio

from graiax import silkcoder
from core.config import config
from core.util.common import make_folder, text_to_pinyin
from core.network.httpRequests import MiraiHttp
from core.database.models import Upload

loop = asyncio.get_event_loop()
mirai_folder = config.miraiApi.folder or 'log'
cache_folder = 'data/net.mamoe.mirai-api-http/voices'


class VoiceManager(MiraiHttp):
    def __init__(self):
        super().__init__()

    def voice(self, path: str, voice_type: str):
        filename = text_to_pinyin(path.split('/')[-1].split('.')[0]) + '.silk'
        group = filename.split('_')[0]
        folder = f'{mirai_folder}/{cache_folder}/{group}'
        target = f'{folder}/{filename}'

        if not os.path.exists(target):
            make_folder(folder)
            loop.run_until_complete(self.silk_encode(path, target))

        # 根据配置支持本地和上传两种模式
        if mirai_folder == 'log':
            rec: Upload = Upload.get_or_none(path=target, type=voice_type)
            if rec:
                return rec.mirai_id, True

            mirai_id = self.get_mirai_id(target, voice_type, _t='voice')

            Upload.create(path=target, type=voice_type, mirai_id=mirai_id)

            return mirai_id, True

        return target, False

    @staticmethod
    async def silk_encode(path, res):
        silk: bytes = await silkcoder.encode(path)
        with open(res, mode='wb+') as file:
            file.write(silk)
