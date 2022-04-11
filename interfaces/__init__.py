from core.network.httpServer.loader import interface
from starlette.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi import Request

from .dashboard import Dashboard
from .replace import Replace
from .admin import Admin, Role
from .group import Group
from .gacha import Pool, Operator
from .user import User
from .bot import Bot

templates = Jinja2Templates(directory='view/dist')


class Index:
    @staticmethod
    @interface.register(router_path='/', method='get', response_class=HTMLResponse)
    async def index_page(request: Request):
        return templates.TemplateResponse('index.html', {'request': request})

    @staticmethod
    @interface.register(router_path='/images', method='get', response_class=StreamingResponse)
    async def images(filename: str):
        return StreamingResponse(open(f'resource/images/temp/{filename}', mode='rb'), media_type='image/png')


controllers = [
    Index,
    Dashboard,
    Operator,
    Replace,
    Admin,
    Group,
    Role,
    Pool,
    User,
    Bot,
]
