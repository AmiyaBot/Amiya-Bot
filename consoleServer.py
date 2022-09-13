import asyncio

from fastapi import Request
from fastapi.responses import HTMLResponse
from amiyabot.network.httpServer import HttpServer
from amiyabot.database import query_to_list
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from core.database.bot import Pool, OperatorConfig, TextReplace

server = HttpServer('0.0.0.0', 80)
server.app.mount('/js', StaticFiles(directory='view/js'), name='js')
server.app.mount('/css', StaticFiles(directory='view/css'), name='css')
server.app.mount('/img', StaticFiles(directory='view/img'), name='img')

templates = Jinja2Templates(directory='view')


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


@server.app.get('/', tags=['Index'], response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


asyncio.run(server.serve())
