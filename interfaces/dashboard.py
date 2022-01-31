import time

from typing import List
from core.network import response
from core.network.httpServer.auth import AuthManager
from core.database.messages import MessageRecord
from core.database.bot import FunctionUsed
from core import account

from functions.user import UserInfo


def get_last_time(hour=24):
    curr_time = int(time.time())
    last_time = curr_time - curr_time % 3600 - hour * 3600
    return last_time


def get_active_users_count(hour):
    last_time = get_last_time(hour)
    return MessageRecord.select().where(MessageRecord.create_time >= last_time,
                                        MessageRecord.msg_type == 'group',
                                        MessageRecord.user_id == account).group_by(MessageRecord.group_id).count()


class Dashboard:
    @classmethod
    async def get_message_analysis(cls, auth=AuthManager.depends()):
        last_time = get_last_time(23)
        now = time.localtime(time.time())
        hour = now.tm_hour

        data: List[MessageRecord] = MessageRecord.select().where(MessageRecord.create_time >= last_time,
                                                                 MessageRecord.msg_type == 'group')
        res = {}

        for i in range(24):
            if hour == 0:
                hour = 24
            res[f'{hour}:00'] = {
                'talk': 0,
                'call': 0,
                'reply': 0
            }
            hour -= 1

        for item in data:
            hour = f'{time.localtime(item.create_time).tm_hour or 24}:00'
            if hour in res:
                res[hour]['talk'] += 1
                if item.user_id == account:
                    res[hour]['reply'] += 1
                if item.classify == 'call':
                    res[hour]['call'] += 1

        return response(res)

    @classmethod
    async def get_function_used(cls, auth=AuthManager.depends()):
        res = [
            {'function_id': item.function_id, 'use_num': item.use_num} for item in FunctionUsed.select()
        ]
        return response(res)

    @classmethod
    async def get_active_users(cls, auth=AuthManager.depends()):
        return response(get_active_users_count(24))

    @classmethod
    async def get_user_sign_rate(cls, auth=AuthManager.depends()):
        hour = time.localtime(time.time()).tm_hour - 4
        if hour < 0:
            hour = 24 + hour

        count = get_active_users_count(hour)
        sign = UserInfo.select().where(UserInfo.sign_in == 1).count()

        return response([count, sign])

    @classmethod
    async def get_message_speed(cls, auth=AuthManager.depends()):
        start = int(time.time()) - 120
        end = int(time.time()) - 60

        count = MessageRecord.select().where(MessageRecord.create_time >= start,
                                             MessageRecord.create_time < end,
                                             MessageRecord.msg_type == 'group').count()

        return response(count)

    @classmethod
    async def get_total_message(cls, auth=AuthManager.depends()):
        last_time = get_last_time()
        count = MessageRecord.select().where(MessageRecord.create_time >= last_time,
                                             MessageRecord.user_id == account).count()

        return response(count)
