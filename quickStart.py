from message.messageHandler import MessageHandler
from modules.gameData import GameData

sender_id = 826197021
group_id = 852191455

message = MessageHandler()


def on_message(text):
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
    try:
        while True:
            message_text = input()

            if message_text == 'update':
                GameData().update()
                continue

            if message_text:
                on_message(message_text)

    except KeyboardInterrupt:
        pass
