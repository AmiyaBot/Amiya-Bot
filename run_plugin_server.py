import asyncio

from amiyabot.log import UserLogger

from amiya import load_resource
from pluginsServer.src import server, api


class Mylogger:
    def info(self, text: str): ...

    def error(self, text: str): ...

    def debug(self, text: str): ...

    def warning(self, text: str): ...

    def critical(self, text: str): ...


UserLogger.logger = Mylogger()

if __name__ == '__main__':
    load_resource()
    asyncio.run(
        server.server.serve()
    )
