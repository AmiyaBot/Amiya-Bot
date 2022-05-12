import json
import aiohttp

from typing import Union
from core import log
from core.util import argv

outline = argv('outline')


class HttpRequests:
    @classmethod
    async def get(cls, interface: str, *args, **kwargs):
        if outline:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(interface, *args, **kwargs) as res:
                    if res.status == 200:
                        return await res.text()
                    else:
                        log.error(f'bad to request <{interface}>[GET]. Got code {res.status}')
        except aiohttp.ClientConnectorError:
            log.error(f'fail to request <{interface}>[GET]')

    @classmethod
    async def post(cls, interface: str, payload: Union[dict, list] = None, headers: dict = None):
        if outline:
            return None

        _headers = {
            'Content-Type': 'application/json',
            **(headers or {})
        }
        _payload = {
            **(payload or {})
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(interface, data=json.dumps(_payload), headers=_headers) as res:
                    if res.status == 200:
                        return await res.text()
                    else:
                        log.error(f'bad to request <{interface}>[POST]. Got code {res.status}')
        except aiohttp.ClientConnectorError:
            log.error(f'fail to request <{interface}>[POST]')

    @classmethod
    async def upload(cls, interface: str, file: bytes, file_field: str = 'file', payload: dict = None):
        if outline:
            return None

        data = aiohttp.FormData()
        data.add_field(file_field,
                       file,
                       content_type='application/octet-stream')

        for field, value in (payload or {}).items():
            data.add_field(field, value)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(interface, data=data) as res:
                    if res.status == 200:
                        return await res.text()
                    else:
                        log.error(f'bad to request <{interface}>[UPLOAD]. Got code {res.status}')
        except aiohttp.ClientConnectorError:
            log.error(f'fail to request <{interface}>[UPLOAD]')


http_requests = HttpRequests
