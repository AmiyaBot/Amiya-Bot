from message.messageHandler import MessageHandler
from modules.config import get_config

message = MessageHandler()


def on_message(text, sender_id, group_id):
    message.on_message({
        'type': 'GroupMessage',
        'messageChain': [
            {
                'type': 'Plain',
                'text': text
            }
        ],
        'sender': {
            'id': sender_id,
            'nickname': 'administrator',
            'memberName': 'administrator',
            'remark': 'none',
            'group': {
                'id': group_id
            }
        }
    })


if __name__ == '__main__':
    print('Testing started.')
    print('Enter a message and press enter to interact.')

    config = get_config()

    try:
        while True:
            message_text = input()
            if message_text:
                on_message(message_text, config['admin_id'], config['close_beta']['group_id'])

    except KeyboardInterrupt:
        pass
