from core import app
from core.util import read_tail


@app.controller
class Dashboard:
    @app.route(method='get')
    async def get_log(self, lines: int = 200):
        return app.response(data=read_tail('log/running.log', lines=lines))
