import uvicorn
import asyncio

from fastapi import FastAPI
from interfaces import controllers
from core.util import snake_case_to_pascal_case

app = FastAPI()
loop = asyncio.get_event_loop()
config = uvicorn.Config(app,
                        loop=loop,
                        host='0.0.0.0',
                        port=5000,
                        log_config='config/server.yaml')
server = uvicorn.Server(config=config)

for cls in controllers:
    attrs = [item for item in dir(cls) if not item.startswith('__')]
    methods = {n: getattr(cls, n) for n in attrs}

    cname = cls.__name__[0].lower() + cls.__name__[1:]

    for name, func in methods.items():
        router = app.post(path=f'/{cname}/{snake_case_to_pascal_case(name)}')
        router(func)
