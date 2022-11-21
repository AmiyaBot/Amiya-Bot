import asyncio

from amiya import load_resource
from pluginsServer.main import server

load_resource()
asyncio.run(server.server.serve())
