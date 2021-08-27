import time

from core import AmiyaBot, Message, Chain
from core.util import log
from core.util.config import config
from core.util.common import TimeRecord
from core.database.models import Message as MessageBase

from handlers import Handlers
from handlers.automaticEvents import AutomaticEvents

limit = config('message.limit')
close_beta = config('closeBeta')


class Main(AmiyaBot):
    def __init__(self):
        tr = TimeRecord()
        log.info(f'starting AmiyaBot...')

        super().__init__()
        self.handlers = Handlers(self)
        self.automaticEvents = AutomaticEvents(self)

        log.info(f'AmiyaBot ready to connect, starting used {tr.rec()} sec.')

    def message_filter(self, data: Message):
        if data.is_admin is False and data.type == 'friend':
            return False

        if data.group_id and close_beta['enable']:
            if str(data.group_id) != str(close_beta['groupId']):
                return False

        for item in ['Q群管家', '小冰']:
            if item in data.text:
                return False

        if data.is_black:
            return False

        speed = MessageBase.select().where(
            MessageBase.user_id == self.account,
            MessageBase.target_id == data.user_id,
            MessageBase.msg_time >= time.time() - limit['seconds']
        )
        if speed.count() >= limit['maxCount']:
            return Chain(data).dont_at().text('博士说话太快了，请慢一些吧～')

        return self.handlers.group_admin_handler(data) if data.type == 'group' else True

    def on_private_message(self, data: Message):
        if data.is_admin:
            return self.handlers.reply_private_message(data)

    def on_group_message(self, data: Message):
        return self.handlers.reply_group_message(data)

    def on_event(self, data: Message):
        self.handlers.event_handler(data)

    def loop_events(self, times):
        self.automaticEvents.exec_all_tasks(times)


if __name__ == '__main__':
    amiya = Main()
    amiya.start()
