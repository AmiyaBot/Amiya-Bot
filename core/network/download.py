import aiohttp
import requests

from io import BytesIO
from core import log
from core.util import argv

outline = argv('outline')
default_headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) '
                  'AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1'
}


def download_sync(url: str, headers=None, stringify=False, progress=False):
    if outline:
        return None

    try:
        stream = requests.get(url, headers=headers or default_headers, stream=True)
        file_size = int(stream.headers['content-length'])

        container = BytesIO()

        if stream.status_code == 200:
            iter_content = stream.iter_content(chunk_size=1024)
            if progress:
                iter_content = log.download_progress(url.split('/')[-1],
                                                     max_size=file_size,
                                                     chunk_size=1024,
                                                     iter_content=iter_content)
            for chunk in iter_content:
                if chunk:
                    container.write(chunk)

            content = container.getvalue()

            if stringify:
                return str(content, encoding='utf-8')
            else:
                return content
    except requests.exceptions.ConnectionError:
        pass
    except Exception as e:
        log.error(e, desc='download error:')


async def download_async(url, headers=None, stringify=False):
    if outline:
        return None

    async with log.catch('download error:', ignore=[requests.exceptions.SSLError]):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers or default_headers) as res:
                if res.status == 200:
                    if stringify:
                        return await res.text()
                    else:
                        return await res.read()
