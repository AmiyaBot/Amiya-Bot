import os

from core.network.download import download_async
from core.resource import resource_config
from core.util import create_dir
from core import log

voices_source = 'resource/voice'


class Wiki:
    @classmethod
    async def download_operator_voices(cls, code, operator, voice, cn=False):
        async with log.catch('voices download error:'):
            filename = f'{operator}_{voice}%s.wav' % ('_cn' if cn else '')
            filepath = f'{voices_source}/{operator}/{filename}'
            url = f'{resource_config.remote.wiki}/voice%s/{code}/{operator}_{voice}.wav' % ('_cn' if cn else '')

            res = await download_async(url)
            if res:
                create_dir(f'{voices_source}/{operator}')
                with open(filepath, mode='wb+') as src:
                    src.write(res)
                return filepath

    @classmethod
    async def check_exists(cls, operator, voice, cn=False):
        file = f'{voices_source}/{operator}/{operator}_{voice}%s.wav' % ('_cn' if cn else '')
        if os.path.exists(file):
            return file
