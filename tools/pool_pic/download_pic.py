import os
import json
import asyncio

from fake_useragent import UserAgent
from amiyabot.network.download import download_async

ua = UserAgent()
path = 'resource/images/pool'

if not os.path.exists(path):
    os.makedirs(path)


async def start():
    with open('pool.json', mode='r', encoding='utf-8') as f:
        pools = json.load(f)

    for item in pools:
        name = item['filename']
        url = item['url']

        if os.path.exists(f'{path}/{name}'):
            continue

        print(f'download {name}')

        res = await download_async(url, headers={'User-Agent': ua.random})
        if res:
            with open(f'{path}/{name}', mode='wb') as f:
                f.write(res)


asyncio.run(start())
