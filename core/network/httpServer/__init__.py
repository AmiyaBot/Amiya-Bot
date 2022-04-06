import os
import asyncio
import uvicorn

from typing import Dict, Callable
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from interfaces import controllers
from core.util import snake_case_to_pascal_case
from core.network.httpServer.auth import AuthManager
from core.database.user import Role, Admin
from core.config import config
from core import log


class HttpServer:
    def __init__(self):
        self.__routes = []

        self.app = FastAPI()
        self.server = self.load_server()
        self.load_controllers()

    def load_controllers(self):
        """
        加载控制器
        """
        for cls in controllers:
            attrs = [item for item in dir(cls) if not item.startswith('__')]
            methods: Dict[str, Callable] = {n: getattr(cls, n) for n in attrs}

            cname = cls.__name__[0].lower() + cls.__name__[1:]

            for name, func in methods.items():
                method = 'post'
                if name.startswith('_'):
                    method = 'get'

                router_path = f'/{cname}/' + snake_case_to_pascal_case(name.strip('_'))
                router_builder = getattr(self.app, method)
                router = router_builder(path=router_path, tags=[cname.title()])
                router(func)

                self.__routes.append(router_path)

        self.app.post(AuthManager.login_url, tags=['Auth'])(AuthManager.login)
        self.app.post(AuthManager.token_url, tags=['Auth'])(AuthManager.token)

    def load_server(self):
        """
        初始化服务
        """
        ssl_key_file = None
        ssl_cert_file = None

        return uvicorn.Server(config=uvicorn.Config(self.app,
                                                    loop='asyncio',
                                                    host=config.httpServer.host,
                                                    port=config.httpServer.port,
                                                    ssl_keyfile=ssl_key_file,
                                                    ssl_certfile=ssl_cert_file,
                                                    log_config='config/private/server.yaml'))

    async def serve(self):
        if Role.get_or_none(id=1):
            Role.update(access_path=','.join(self.__routes)).where(Role.id == 1).execute()
        else:
            Role.create(
                id=1,
                role_name='超级管理员',
                access_path=','.join(self.__routes),
                active=1
            )

        for item in config.admin.accounts:
            if not Admin.get_or_none(user_id=item):
                Admin.create(
                    user_id=item,
                    role_id=1,
                    password='admin123',
                    active=1
                )

        if not os.path.exists('view'):
            await asyncio.sleep(5)

        async with log.catch('Http server Error:'):
            # 加载静态文件
            self.app.mount('/static', StaticFiles(directory='view/dist/static'), name='static')

            # 设置跨域请求
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=['*'],
                allow_methods=['*'],
                allow_headers=['*'],
                allow_credentials=True
            )

            # 加载模板
            templates = Jinja2Templates(directory='view/dist')

            @self.app.get('/', tags=['Index'], response_class=HTMLResponse)
            async def index(request: Request):
                return templates.TemplateResponse('index.html', {'request': request})

            @self.app.get('/images', tags=['Image'], response_class=StreamingResponse)
            async def index(filename: str):
                return StreamingResponse(open(f'resource/images/temp/{filename}', mode='rb'), media_type='image/png')

            await self.server.serve()
