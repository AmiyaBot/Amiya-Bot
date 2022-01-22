import os
import asyncio
import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from interfaces import controllers
from core.util import snake_case_to_pascal_case
from core import log


class HttpServer:
    def __init__(self, host: str = '127.0.0.1', port: int = 5000):
        self.app = FastAPI()
        self.server = self.load_server(host, port)
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
                router = self.app.post(path=f'/{cname}/{snake_case_to_pascal_case(name)}')
                router(func)

    def load_server(self, host, port):
        """
        初始化服务
        """
        config = uvicorn.Config(self.app,
                                host=host,
                                port=port,
                                loop='asyncio',
                                log_config='config/private/server.yaml')

        return uvicorn.Server(config=config)

    async def serve(self):
        if not os.path.exists('view'):
            await asyncio.sleep(5)

        async with log.catch('Http server Error:'):
            # 加载静态文件
            self.app.mount('/static', StaticFiles(directory='view/static'), name='static')

            # 加载模板
            templates = Jinja2Templates(directory='view')

            @self.app.get('/', response_class=HTMLResponse)
            async def index(request: Request):
                return templates.TemplateResponse('index.html', {'request': request})

            await self.server.serve()
