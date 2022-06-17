from core.network.mirai.websocketClient import WebsocketClient, account
from core.network.mirai.httpClient import HttpClient
from core.builtin.htmlConverter import ChromiumBrowser
from core.builtin.timedTask import TasksControl
from core.database.messages import MessageStack

from core.builtin.message import Message, Event
from core.builtin.messageChain import Chain, custom_chain
from core.builtin.message.mirai import Mirai
from core.builtin.messageHandler import speed

from core.resource.botResource import BotResource
from core.resource.arknightsGameData import ArknightsGameDataResource, ArknightsGameData

http = HttpClient()
websocket = WebsocketClient()
init_task = [
    ChromiumBrowser().launch
]


async def initialization():
    # BotResource.download_bot_resource()
    # BotResource.download_amiya_bot_console()
    # ArknightsGameDataResource.download_gamedata_files()

    for coro in init_task:
        await coro()


def exec_before_init(coro):
    init_task.append(coro)
    return coro


def init_core():
    return [
        initialization(),
        http.init_session(),
        websocket.connect_websocket(),
        speed.clean_container(),
        MessageStack.run_recording(),
        TasksControl.run_tasks(websocket)
    ]
