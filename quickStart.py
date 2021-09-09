from core.util.config import config
from core.util import log
from core import Message

from amiya import Main


class QuickStart:
    def __init__(self):
        self.config = config()
        self.type = 'group'

        if self.config['offline'] is not True:
            raise Exception('discontinued starting because config <offline> should be "True".')

        self.bot = Main()

    def message(self, text):
        return Message(
            {
                'type': 'GroupMessage' if self.type == 'group' else 'FriendMessage',
                'messageChain': [
                    {
                        'type': 'Plain',
                        'text': text
                    }
                ],
                'sender': {
                    'id': self.config['adminId'],
                    'permission': 'OWNER',
                    'nickname': 'OWNER',
                    'memberName': 'OWNER',
                    'remark': 'none',
                    'group': {
                        'id': self.config['closeBeta']['groupId']
                    }
                }
            }
        )

    def change_type(self, text):
        if text in ['group', 'friend']:
            self.type = text
            log.info(f'message type change to {text}.')
            return False
        return True

    def start(self):
        try:
            log.info('input the message to test.')
            while True:
                text = input(f'{self.type} message: ')
                if self.change_type(text):
                    res = self.bot.on_group_message(self.message(text))
                    if res:
                        self.bot.send_message(res)
        except KeyboardInterrupt:
            pass

    def unit_test(self, text):
        res = self.bot.on_group_message(self.message(text))
        if res:
            self.bot.send_message(res)


if __name__ == '__main__':
    s = QuickStart()

    # console 测试
    s.bot.console.start()

    # 对话式测试
    # s.start()

    # 快速测试单句指令
    # s.unit_test('兔兔语音阿米娅闲置')
