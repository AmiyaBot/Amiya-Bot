import aiohttp
import requests

from core import log

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) '
                  'AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1'
}


def download_sync(url, stringify=True):
    try:
        stream = requests.get(url, headers=headers, stream=True)
        if stream.status_code == 200:
            if stringify:
                return str(stream.content, encoding='utf-8')
            else:
                return stream.content
    except Exception as e:
        log.error(e, desc='download error:')


async def download_async(url, stringify=True):
    async with log.catch('download error:'):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as res:
                if res.status == 200:
                    if stringify:
                        return await res.text()
                    else:
                        return await res.read()
