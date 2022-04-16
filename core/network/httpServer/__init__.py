import os
import asyncio
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from interfaces import controllers
from core.network.httpServer.auth import AuthManager
from core.network.httpServer.loader import interface
from core.config import config
from core import log


class HttpServer:
    def __init__(self):
        self.__routes = []

        self.app = FastAPI(title='AmiyaBot Console Interfaces',
                           description='AmiyaBot 后台管理系统接口，https://www.amiyabot.com/docs/amiyaConsole.html')
        self.server = self.load_server()
        self.load_controllers()

    def load_controllers(self):
        """
        加载控制器
        """
        for cls in controllers:
            for fn, router_path, method, cname, options in interface.load_controller(cls):
                arguments = {
                    'path': router_path,
                    'tags': [cname.title()],
                    **options
                }

                router_builder = getattr(self.app, method)
                router = router_builder(**arguments)
                router(fn)

                if cname != 'index':
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
        await AuthManager.set_super_admin(','.join(self.__routes))

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

            await self.server.serve()
