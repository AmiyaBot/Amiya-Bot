import os
import urllib.parse

from requests_html import HTMLSession, HTML
from core.network.download import download_async
from core.util import create_dir, run_in_thread_pool
from core import log

voices_source = 'resource/voice'


class Wiki:
    @classmethod
    def get_page(cls, url):
        req = HTMLSession().get(url)
        return getattr(req, 'html')

    @classmethod
    async def get_voice_urls(cls, name):
        html: HTML = await run_in_thread_pool(cls.get_page, f'http://prts.wiki/w/{name}/语音记录')
        files = {}
        for item in html.find('a[download]'):
            url = 'http:' + urllib.parse.unquote(item.attrs['href'])
            file_name = url.split('/')[-1]
            files[file_name] = url
        return files

    @classmethod
    async def download_voice(cls, operator, url, filename):
        file = f'{voices_source}/{operator}/{filename}'

        res = await download_async(url)
        if res:
            create_dir(f'{voices_source}/{operator}')
            with open(file, mode='wb+') as src:
                src.write(res)
            return file

    @classmethod
    async def download_operator_voices(cls, operator, name):
        async with log.catch('voices download error:'):
            urls = await cls.get_voice_urls(operator)
            filename = f'{operator}_{name}.wav'
            if filename in urls:
                return await cls.download_voice(operator, urls[filename], filename)

    @classmethod
    async def check_exists(cls, operator, name):
        file = f'{voices_source}/{operator}/{operator}_{name}.wav'
        if os.path.exists(file):
            return file
