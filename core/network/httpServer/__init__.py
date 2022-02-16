import os
import asyncio
import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from interfaces import controllers
from core.util import snake_case_to_pascal_case
from core.network.httpServer.auth import AuthManager
from core.config import config
from core import log


class HttpServer:
    def __init__(self):
        self.app = FastAPI()
        self.server = self.load_server()
        self.load_controllers()

    def load_controllers(self):
        """
        加载控制器
        """
        for cls in controllers:
            attrs = [item for item in dir(cls) if not item.startswith('__')]
            methods = {n: getattr(cls, n) for n in attrs}

            cname = cls.__name__[0].lower() + cls.__name__[1:]

            for name, func in methods.items():
                router = self.app.post(path=f'/{cname}/{snake_case_to_pascal_case(name)}', tags=[cname.title()])
                router(func)

        self.app.post(AuthManager.login_url, tags=['Auth'])(AuthManager.login)
        self.app.post(AuthManager.token_url, tags=['Auth'])(AuthManager.token)

    def load_server(self):
        """
        初始化服务
        """
        ssl_key_file = None
        ssl_cert_file = None

        if config.httpServer.https:
            ssl_key_file = 'resource/certificate/key.pem'
            ssl_cert_file = 'resource/certificate/cert.pem'

        return uvicorn.Server(config=uvicorn.Config(self.app,
                                                    loop='asyncio',
                                                    host=config.httpServer.host,
                                                    port=config.httpServer.port,
                                                    ssl_keyfile=ssl_key_file,
                                                    ssl_certfile=ssl_cert_file,
                                                    log_config='config/private/server.yaml'))

    async def serve(self):
        if not os.path.exists('view'):
            await asyncio.sleep(5)

        async with log.catch('Http server Error:'):
            # 加载静态文件
            self.app.mount('/static', StaticFiles(directory='view/static'), name='static')

            # 设置跨域请求
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=['*'],
                allow_methods=['*'],
                allow_headers=['*'],
                allow_credentials=True
            )

            # 加载模板
            templates = Jinja2Templates(directory='view')

            @self.app.get('/', tags=['Index'], response_class=HTMLResponse)
            async def index(request: Request):
                return templates.TemplateResponse('index.html', {'request': request})

            @self.app.get('/images', tags=['Image'], response_class=StreamingResponse)
            async def index(filename: str):
                return StreamingResponse(open(f'resource/images/temp/{filename}', mode='rb'), media_type='image/png')

            await self.server.serve()
