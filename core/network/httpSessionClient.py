import os
import json
import aiohttp

from core import log
from core.util import singleton, create_dir
from core.config import config

session_file = 'fileStorage/session.txt'
create_dir(session_file, is_file=True)


@singleton
class HttpSessionClient:
    def __init__(self):
        self.host = f'{config.miraiApiHttp.host}:{config.miraiApiHttp.port.http}'
        self.session = None

    def __url(self, interface):
        return 'http://%s/%s' % (self.host, interface)

    @staticmethod
    def __json(interface, res):
        try:
            response = json.loads(res)
            if response['code'] != 0:
                log.error(f'http </{interface}> response: {response}')
                return None
            return response
        except json.decoder.JSONDecodeError:
            return res

    async def get(self, interface):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.__url(interface)) as res:
                    if res.status == 200:
                        return self.__json(interface, await res.text())
                    else:
                        log.error(f'bad to request </{interface}>[GET]. Got code {res.status}')
        except aiohttp.ClientConnectorError:
            log.error(f'fail to request </{interface}>[GET]')

    async def post(self, interface, data):
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.__url(interface), data=json.dumps(data), headers=headers) as res:
                    if res.status == 200:
                        return self.__json(interface, await res.text())
                    else:
                        log.error(f'bad to request </{interface}>[POST]. Got code {res.status}')
        except aiohttp.ClientConnectorError:
            log.error(f'fail to request </{interface}>[POST]')

    async def upload(self, interface, field, file, msg_type):
        data = aiohttp.FormData()
        data.add_field('sessionKey', self.session)
        data.add_field('type', msg_type)
        data.add_field(field,
                       file,
                       content_type='application/octet-stream')

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.__url(interface), data=data) as res:
                    if res.status == 200:
                        return json.loads(await res.text())
                    else:
                        log.error(f'bad to request </{interface}>[UPLOAD]. Got code {res.status}')
        except aiohttp.ClientConnectorError:
            log.error(f'fail to request </{interface}>[UPLOAD]')

    async def upload_image(self, file, msg_type):
        res = await self.upload('uploadImage', 'img', file, msg_type)
        if 'imageId' in res:
            return res['imageId']

    async def upload_voice(self, file, msg_type):
        res = await self.upload('uploadVoice', 'voice', file, msg_type)
        if 'voiceId' in res:
            return res['voiceId']

    async def init_session(self):
        response = await self.post('verify', {'verifyKey': config.miraiApiHttp.authKey})
        if response:
            self.session = response['session']

            log.info('http verify successful. session: ' + self.session)

            if os.path.exists(session_file):
                with open(session_file, mode='r+') as sf:
                    await self.post('release',
                                    {'sessionKey': sf.read().strip('\n '), 'qq': config.miraiApiHttp.account})

            await self.post('bind', {'sessionKey': self.session, 'qq': config.miraiApiHttp.account})

            with open(session_file, mode='w+') as sf:
                sf.write(self.session)

            return self.session

    async def get_group_list(self):
        response = await self.get(f'groupList?sessionKey={self.session}')
        if response:
            group_list = {}
            for item in response['data']:
                if item['id'] not in group_list:
                    group_list[item['id']] = {
                        'group_id': item['id'],
                        'group_name': item['name'],
                        'permission': item['permission']
                    }
            group_list = [n for i, n in group_list.items()]
            return group_list
        return []
