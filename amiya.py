from modules.network.websocketClient import Websocket
from modules.network.httpRequests import HttpRequests
from modules.automaticAction import run_automatic_action
from message.messageHandler import MessageHandler

message = MessageHandler()
http = HttpRequests()


def run_websocket_client():
    try:
        session = http.get_session()
        websocket = Websocket(session, handler=message.on_message)
        websocket.run_forever()
    except Exception as e:
        print('Websocket', e)
        run_websocket_client()


if __name__ == '__main__':
    http.init_session()
    run_automatic_action()
    run_websocket_client()
