from core.network.websocketClient import WebsocketClient
from core.network.httpSessionClient import HttpSessionClient
from core.builtin.message import Message, Event
from core.builtin.messageChain import Chain, custom_chain
from core.builtin.message.mirai import Mirai

http = HttpSessionClient()
websocket = WebsocketClient()


def network():
    return [
        http.init_session(),
        websocket.connect_websocket(),
    ]
