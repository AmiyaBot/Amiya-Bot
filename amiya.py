from core import AmiyaBot, Message
from core.util import log
from core.util.common import TimeRecord

from console.server.app import Console
from handlers.messageHandlers import Handlers
from handlers.automaticEvents import AutomaticEvents


class Main(AmiyaBot):
    def __init__(self):
        tr = TimeRecord()
        log.info(f'starting AmiyaBot...')

        super().__init__()
        self.handlers = Handlers(self)
        self.automaticEvents = AutomaticEvents(self)

        log.info(f'AmiyaBot ready to connect, starting used {tr.rec()} sec.')

    def message_filter(self, data: Message):
        return self.handlers.filter_handler(data)

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
    Main().start()
    Console().start()
