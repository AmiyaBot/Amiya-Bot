from core.network.websocketClient import WebsocketClient, account
from core.network.httpSessionClient import HttpSessionClient
from core.database.messages import MessageStack
from core.builtin.timedTask import TasksControl

from core.builtin.message import Message, Event
from core.builtin.messageChain import Chain, custom_chain
from core.builtin.message.mirai import Mirai
from core.builtin.messageHandler import speed

from core.resource.botResource import BotResource
from core.resource.arknightsGameData import ArknightsGameDataResource, ArknightsGameData

http = HttpSessionClient()
websocket = WebsocketClient()
init_task = []


async def download_files():
    BotResource.download_bot_resource()
    BotResource.download_amiya_bot_console()
    ArknightsGameDataResource.download_data_fiels()
    ArknightsGameDataResource.download_operators_resource()
    ArknightsGameDataResource.download_materials_resource()
    ArknightsGameDataResource.download_enemies_resource()
    ArknightsGameDataResource.refresh_download_ignore()

    for coro in init_task:
        await coro()


def exec_before_init(coro):
    init_task.append(coro)
    return coro


def init_core():
    return [
        download_files(),
        http.init_session(),
        websocket.connect_websocket(),
        speed.clean_container(),
        MessageStack.run_recording(),
        TasksControl.run_tasks(websocket)
    ]
