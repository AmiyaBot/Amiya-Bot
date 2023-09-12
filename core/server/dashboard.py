import time

from typing import List

from core import app
from core.util import read_tail
from core.database.bot import FunctionUsed, query_to_list
from core.database.messages import MessageRecord


def get_last_time(hour: int = 24):
    curr_time = int(time.time())
    last_time = curr_time - curr_time % 3600 - hour * 3600
    return last_time


@app.controller
class Dashboard:
    @app.route(method='get')
    async def get_log(self, lines: int = 200):
        return app.response(data=read_tail('log/running.log', lines=lines))

    @app.route(method='get')
    async def get_functions_used(self):
        return app.response(data=query_to_list(FunctionUsed.select()))

    @app.route(method='get')
    async def get_message_record(self, appid: str):
        last_time = get_last_time(23)
        now = time.localtime(time.time())
        hour = now.tm_hour

        data: List[MessageRecord] = MessageRecord.select().where(
            MessageRecord.app_id == appid, MessageRecord.create_time >= last_time
        )
        res = {}

        for i in range(24):
            if hour == 0:
                hour = 24
            res[f'{hour}:00'] = {'call': 0, 'user': [], 'channel': []}
            hour -= 1

        for item in data:
            hour = f'{time.localtime(item.create_time).tm_hour or 24}:00'
            if hour in res:
                res[hour]['call'] += 1

                if item.user_id not in res[hour]['user']:
                    res[hour]['user'].append(item.user_id)

                if item.channel_id not in res[hour]['channel']:
                    res[hour]['channel'].append(item.channel_id)

        for _, item in res.items():
            item['user'] = len(item['user'])
            item['channel'] = len(item['channel'])

        return app.response(res)
