import json

from core import log
from core.network.mirai import HttpAdapter
from core.network.httpRequests import http_requests
from core.database.group import Group, GroupActive, GroupSetting
from core.database.bot import Session
from core.config import config


class HttpClient:
    def __init__(self, account):
        self.host = f'{config.miraiApiHttp.host}:{config.miraiApiHttp.port.http}'
        self.account = account
        self.session = None

    @staticmethod
    def __json(interface, res):
        try:
            response = json.loads(res)
            if response['code'] != 0:
                log.error(f'http <{interface}> response: {response}')
                return None
            return response
        except json.decoder.JSONDecodeError:
            return res

    def __url(self, interface):
        return 'http://%s/%s' % (self.host, interface)

    async def get(self, interface):
        res = await http_requests.get(self.__url(interface))
        if res:
            return self.__json(interface, res)

    async def post(self, interface, data):
        res = await http_requests.post(self.__url(interface), data)
        if res:
            return self.__json(interface, res)

    async def upload(self, interface, field_type, file, msg_type):
        res = await http_requests.upload(self.__url(interface), file, file_field=field_type, payload={
            'sessionKey': self.session,
            'type': msg_type
        })
        if res:
            return json.loads(res)

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

            log.info(f'{self.account} verify successful. session: {self.session}')

            record: Session = Session.get_or_none(account=self.account)
            if record:
                await self.post('release', {'sessionKey': record.session, 'qq': self.account})
                Session.update(session=self.session).where(Session.account == self.account).execute()
            else:
                Session.create(session=self.session, account=self.account)

            await self.post('bind', {'sessionKey': self.session, 'qq': self.account})

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

    async def leave_group(self, group_id, flag=True):
        if flag:
            await self.post('quit', {'sessionKey': self.session, 'target': group_id})

        Group.delete().where(Group.group_id == group_id).execute()
        GroupActive.delete().where(GroupActive.group_id == group_id).execute()
        GroupSetting.delete().where(GroupSetting.group_id == group_id).execute()

    async def send_nudge(self, user_id, group_id):
        await self.post('sendNudge', HttpAdapter.nudge(self.session, user_id, group_id))
