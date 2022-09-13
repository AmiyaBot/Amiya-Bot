import json

from amiyabot import log
from amiyabot.network.httpRequests import http_requests
from core.resource import remote_config
from core.database.bot import PenguinData


async def save_penguin_data():
    async with log.catch('penguin data save error:'):
        res = await http_requests.get(remote_config.remote.penguin)
        res = json.loads(res)

        PenguinData.truncate_table()
        PenguinData.batch_insert(res['matrix'])
