import os
import json
import requests

from database.baseController import BaseController
from modules.config import get_config

database = BaseController()

config = get_config()
self_id = str(config['self_id'])
admin_id = str(config['admin_id'])
session_file = 'temp/session.txt'


class HttpRequests:
    def __init__(self):
        self.request = requests.session()
        self.config = config

    def url(self, interface):
        return 'http://%s:%d/%s' % (self.config['server']['server_ip'], self.config['server']['server_port'], interface)

    def post(self, interface, data):
        response = self.request.post(self.url(interface), data=json.dumps(data), headers={
            'Content-Type': 'application/json'
        })
        if response.status_code == 200:
            return json.loads(response.text)
        return False

    def get(self, interface):
        response = self.request.get(self.url(interface))
        if response.status_code == 200:
            return json.loads(response.text)
        return False

    def init_session(self):
        response = self.post('auth', {'authKey': config['server']['auth_key']})
        session = response['session']

        session_record = self.get_session()
        if session_record:
            self.post('release', {'sessionKey': session_record, 'qq': self_id})

        self.post('verify', {'sessionKey': session, 'qq': self_id})

        with open(session_file, mode='w+') as session_record:
            session_record.write(session)

    @staticmethod
    def get_session():
        if os.path.exists(session_file):
            with open(session_file, mode='r+') as session_record:
                session = session_record.read()
                if session:
                    return session
        return ''

    def get_group_list(self):
        if config['close_beta']['enable']:
            return [{'id': config['close_beta']['group_id']}]

        session = self.get_session()
        if session:
            response = self.get('groupList?sessionKey=%s' % session)
            return response
        return []

    def handle_join_group(self, data, operate):
        self.post('/resp/botInvitedJoinGroupRequestEvent', {
            'sessionKey': self.get_session(),
            'eventId': data['eventId'],
            'fromId': data['fromId'],
            'groupId': data['groupId'],
            'operate': 1 if operate else 0,
            'message': ''
        })

    def leave_group(self, group_id, flag=True):
        if flag:
            session = self.get_session()
            self.post('quit', {'sessionKey': session, 'target': group_id})

    def send_private_message(self, data, message='', message_chain=None):
        session = self.get_session()
        if message_chain and type(message_chain) is list:
            chain = message_chain
        else:
            chain = [{
                'type': 'Plain',
                'text': message
            }]

        self.post('sendFriendMessage', {
            'sessionKey': session,
            'target': data['user_id'],
            'messageChain': chain
        })

    def send_group_message(self, data, message='', message_chain=None, at=False):
        session = self.get_session()
        if message_chain and type(message_chain) is list:
            chain = message_chain
        else:
            chain = [{
                'type': 'Plain',
                'text': message
            }]
        if at:
            chain.insert(0, {'type': 'Plain', 'text': '\n'})
            chain.insert(0,
                         {'type': 'AtAll', 'target': 0} if at == 'all' else {'type': 'At', 'target': data['user_id']})

        self.post('sendGroupMessage', {
            'sessionKey': session,
            'target': data['group_id'],
            'messageChain': chain
        })

    def send_message(self, data, message='', message_chain=None, at=False):

        database.message.add_message(self_id, 'reply', reply_user=data['user_id'])

        if data['type'] == 'group':
            self.send_group_message(data, message=message, message_chain=message_chain, at=at)
        else:
            self.send_private_message(data, message=message, message_chain=message_chain)

    def send_admin(self, text):
        self.send_private_message({'user_id': admin_id}, text)
