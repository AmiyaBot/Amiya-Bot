from core.network.websocketClient import WebsocketClient
from core.network.httpSessionClient import HttpSessionClient
from core.builtin.message import Message, Event
from core.builtin.messageChain import Chain, custom_chain
from core.builtin.message.mirai import Mirai
from resourceCenter.resourceManager import ResourceManager as Resource

http = HttpSessionClient()
websocket = WebsocketClient()

Resource.download_amiya_bot_console()


def network():
    return [
        http.init_session(),
        websocket.connect_websocket(),
    ]
