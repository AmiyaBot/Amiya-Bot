from core.network.websocketClient import WebsocketClient
from core.network.httpSessionClient import HttpSessionClient

from core.builtin.message import Message, Event
from core.builtin.messageChain import Chain, custom_chain
from core.builtin.message.mirai import Mirai

from core.resource.botResource import BotResource
from core.resource.arknightsGameData import ArknightsGameDataResource

http = HttpSessionClient()
websocket = WebsocketClient()

BotResource.download_bot_resource()
BotResource.download_amiya_bot_console()
ArknightsGameDataResource.download_data_fiels()


def network():
    return [
        http.init_session(),
        websocket.connect_websocket(),
    ]
