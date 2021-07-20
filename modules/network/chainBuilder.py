from database.baseController import BaseController
from modules.config import get_config

database = BaseController()
self_id = get_config('self_id')


class Chain:
    def __init__(self, session, data, message, message_chain, at):
        self.session = session
        self.data = data
        self.message = message
        self.message_chain = message_chain
        self.at = at

    def content(self):
        if self.data['type'] == 'group':
            content = self.__group_message()
            command = 'sendGroupMessage'

            if 'user_id' in self.data:
                database.message.add_message(msg_type='reply', user_id=self_id, reply_user=self.data['user_id'])
        else:
            content = self.__private_message()
            command = 'sendFriendMessage'

        return command, content

    def __private_message(self):
        if self.message_chain and type(self.message_chain) is list:
            chain = self.message_chain
        else:
            chain = [{
                'type': 'Plain',
                'text': self.message
            }]

        return {
            'sessionKey': self.session,
            'target': self.data['user_id'],
            'messageChain': chain
        }

    def __group_message(self):
        if self.message_chain and type(self.message_chain) is list:
            chain = self.message_chain
        else:
            chain = [{
                'type': 'Plain',
                'text': self.message
            }]

        if self.at:
            at_all = {'type': 'AtAll', 'target': 0}
            at_user = {'type': 'At', 'target': self.data['user_id']}

            chain.insert(0, {'type': 'Plain', 'text': '\n'})
            chain.insert(0, at_all if self.at == 'all' else at_user)

        return {
            'sessionKey': self.session,
            'target': self.data['group_id'],
            'messageChain': chain
        }
