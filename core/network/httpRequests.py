import os
import json
import requests

from core.database.models import Group
from core.util.config import config
from core.util import log

session_file = 'session.txt'


class MiraiHttp:
    def __init__(self):
        server = config('server')

        self.offline = config('offline')

        self.host = f'{server["serverIp"]}:{server["httpPort"]}'
        self.auth_key = server['authKey']
        self.request = requests.session()
        self.session = self.get_session()

    def __url(self, interface):
        return 'http://%s/%s' % (self.host, interface)

    def __post(self, interface, data):
        response = self.request.post(self.__url(interface), data=json.dumps(data), headers={
            'Content-Type': 'application/json'
        })
        if response.status_code == 200:
            return json.loads(response.text)
        return False

    def __get(self, interface):
        response = self.request.get(self.__url(interface))
        if response.status_code == 200:
            return json.loads(response.text)
        return False

    def init_session(self):
        if self.offline:
            log.info('http offline.')
            return True
        try:
            response: dict = self.__post('verify', {'verifyKey': self.auth_key})
            if response:
                if response['code'] != 0:
                    log.error('mirai-api-http response: ' + response['msg'])
                    return False

                session = response['session']
                self_id = config('selfId')

                log.info('init http session: ' + session)

                session_record = self.get_session()
                if session_record:
                    log.info('release session: ' + session_record)
                    self.__post('release', {'sessionKey': session_record, 'qq': self_id})

                self.__post('bind', {'sessionKey': session, 'qq': self_id})

                with open(session_file, mode='w+') as sf:
                    sf.write(session)

                self.session = session
                return True
        except Exception as e:
            log.error(repr(e))

        return False

    def get_image_id(self, multipart_data):
        if self.offline:
            return 'None'

        response = self.request.post(
            url=self.__url('uploadImage'),
            data=multipart_data,
            headers={
                'Content-Type': multipart_data.content_type
            }
        )
        if response.status_code == 200:
            data = json.loads(response.text)
            return data['imageId']
        return False

    def get_group_list(self):
        beta = config('closeBeta')
        if beta['enable']:
            return [
                {
                    'id': beta['groupId']
                }
            ]
        else:
            response = self.__get('groupList?sessionKey=%s' % self.session)
            if response and response['code'] == 0:
                group_list = {}
                for item in response['data']:
                    if item['id'] not in group_list:
                        group_list[item['id']] = item
                group_list = [n for i, n in group_list.items()]
                return group_list
            return []

    def handle_join_group(self, event, allow=True):
        self.__post('/resp/botInvitedJoinGroupRequestEvent', {
            'sessionKey': self.session,
            'eventId': event['eventId'],
            'fromId': event['fromId'],
            'groupId': event['groupId'],
            'operate': 0 if allow else 1,
            'message': ''
        })

    def leave_group(self, group_id, flag=True):
        if flag:
            self.__post('quit', {'sessionKey': self.session, 'target': group_id})
        Group.delete().where(Group.group_id == group_id).execute()

    @staticmethod
    def get_session():
        if os.path.exists(session_file):
            with open(session_file, mode='r+') as session_record:
                session = session_record.read()
                if session:
                    return session
        return ''


class DownloadTools:
    @staticmethod
    def request_file(url, stringify=True):
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) '
                          'AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1'
        }
        try:
            stream = requests.get(url, headers=headers, stream=True)
            if stream.status_code == 200:
                if stringify:
                    return str(stream.content, encoding='utf-8')
                else:
                    return stream.content
        except Exception as e:
            log.error(repr(e))
        return False
