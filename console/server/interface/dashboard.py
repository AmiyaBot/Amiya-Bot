import time

from flask import Flask

from core.database.models import Message, Function, User
from core.config import config

from ..response import response

account = config.account.bot


def get_last_time(hour=24):
    curr_time = int(time.time())
    last_time = curr_time - curr_time % 3600 - hour * 3600
    return last_time


def get_active_users_count(hour):
    last_time = get_last_time(hour)
    condition = Message.msg_time >= last_time, Message.msg_type == 'group', Message.user_id == account
    return Message.select().where(*condition).group_by(Message.target_id).count()


def dashboard_controller(app: Flask):
    @app.route('/dashboard/getMessageAnalysis', methods=['POST'])
    def get_message_analysis():
        last_time = get_last_time(23)
        now = time.localtime(time.time())
        hour = now.tm_hour

        data = Message.select().where(Message.msg_time >= last_time, Message.msg_type == 'group')
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
            item: Message
            hour = f'{time.localtime(item.msg_time).tm_hour or 24}:00'
            if hour in res:
                res[hour]['talk'] += 1
                if item.user_id == account:
                    res[hour]['reply'] += 1
                if item.record == 'call':
                    res[hour]['call'] += 1

        return response(res)

    @app.route('/dashboard/getFunctionUsed', methods=['POST'])
    def get_function_used():
        res = [
            {'function_id': item.function_id, 'use_num': item.use_num} for item in Function.select()
        ]

        return response(res)

    @app.route('/dashboard/getActiveUsers', methods=['POST'])
    def get_active_users():
        return response(get_active_users_count(24))

    @app.route('/dashboard/getUserSignRate', methods=['POST'])
    def get_user_sign_rate():
        hour = time.localtime(time.time()).tm_hour - 4
        if hour < 0:
            hour = 24 + hour

        count = get_active_users_count(hour)
        sign = User.select().where(User.sign_in == 1).count()

        return response([count, sign])

    @app.route('/dashboard/getMessageSpeed', methods=['POST'])
    def get_message_speed():
        start = int(time.time()) - 120
        end = int(time.time()) - 60

        count = Message.select().where(Message.msg_time >= start,
                                       Message.msg_time < end,
                                       Message.msg_type == 'group').count()

        return response(count)

    @app.route('/dashboard/getTotalMessage', methods=['POST'])
    def get_total_message():
        last_time = get_last_time()
        count = Message.select().where(Message.msg_time >= last_time, Message.user_id == account).count()

        return response(count)
