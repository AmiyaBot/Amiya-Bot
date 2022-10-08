import asyncio

from amiyabot.network.httpServer import HttpServer
from amiyabot.database import query_to_list
from core.database.bot import Pool, OperatorConfig, TextReplace

server = HttpServer('0.0.0.0', 8000)


@server.route(method='get', router_path='/pool/getPool')
async def get_gacha_pool():
    data = {
        'Pool': query_to_list(Pool.select()),
        'OperatorConfig': query_to_list(OperatorConfig.select())
    }
    return server.response(data=data)


@server.route(method='get', router_path='/replace/getReplace')
async def get_replace():
    return server.response(data=query_to_list(TextReplace.select()))


asyncio.run(server.serve())
