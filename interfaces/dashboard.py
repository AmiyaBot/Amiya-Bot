import time

from typing import List
from core.network import response
from core.network.httpServer.loader import interface
from core.network.httpServer.auth import AuthManager
from core.database.messages import MessageRecord
from core.database.bot import FunctionUsed
from core import account


def get_last_time(hour=24):
    curr_time = int(time.time())
    last_time = curr_time - curr_time % 3600 - hour * 3600
    return last_time


def get_active_users_count(hour):
    last_time = get_last_time(hour)
    return MessageRecord.select().where(MessageRecord.create_time >= last_time,
                                        MessageRecord.msg_type == 'group',
                                        MessageRecord.classify == 'call').group_by(MessageRecord.user_id).count()


class DashboardCache:
    cache = {}

    @classmethod
    def set_cache(cls, cache_name, data):
        cls.cache[cache_name] = (time.time(), data)
        return data

    @classmethod
    def get_cache(cls, cache_name):
        if cache_name in cls.cache:
            now = time.time()
            if now - cls.cache[cache_name][0] <= 300:
                return cls.cache[cache_name][1]


class Dashboard:
    @staticmethod
    @interface.register()
    async def get_message_analysis(auth=AuthManager.depends()):
        if DashboardCache.get_cache('message_analysis'):
            return response(DashboardCache.get_cache('message_analysis'))

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

        return response(DashboardCache.set_cache('message_analysis', res))

    @staticmethod
    @interface.register()
    async def get_function_used(auth=AuthManager.depends()):
        if DashboardCache.get_cache('function_used'):
            return response(DashboardCache.get_cache('function_used'))

        res = [
            {'function_id': item.function_id, 'use_num': item.use_num} for item in FunctionUsed.select()
        ]

        return response(DashboardCache.set_cache('function_used', res))

    @staticmethod
    @interface.register()
    async def get_real_time_data(auth=AuthManager.depends()):
        if DashboardCache.get_cache('real_time_data'):
            return response(DashboardCache.get_cache('real_time_data'))

        return response(DashboardCache.set_cache('real_time_data', {
            'reply': MessageRecord.select().where(MessageRecord.create_time >= get_last_time(),
                                                  MessageRecord.user_id == account).count(),
            'speed': MessageRecord.select().where(MessageRecord.create_time >= int(time.time()) - 120,
                                                  MessageRecord.create_time < int(time.time()) - 60,
                                                  MessageRecord.msg_type == 'group').count(),
            'activeUsers': get_active_users_count(24)
        }))
