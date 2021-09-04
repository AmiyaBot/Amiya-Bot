import os
import sys
import abc
import time
import threading

from core.network.websocket import WebSocket
from core.network.httpRequests import MiraiHttp
from core.resolver.message import Message
from core.resolver.messageChain import Chain
from core.database.manager import DataBase, Message as MessageBase
from core.util import log


class AmiyaBot(WebSocket):
    handlers = None

    def __init__(self):
        super().__init__()

        DataBase.create_base()

        self.message_stack = []
        self.http = MiraiHttp()

        init = self.http.init_session()
        if init is False:
            raise Exception(f'cannot request http server from mirai-api-http.')

    def __save_message(self):
        while True:
            if self.message_stack:
                MessageBase.insert_many(self.message_stack)
                self.message_stack = []
            time.sleep(30)

    def __loop_machine(self):
        t = 1
        while True:
            self.executor.put(self.loop_events, t, self.traceback_error)
            t += 1
            time.sleep(30)

    def opened(self):
        threading.Thread(target=self.__save_message).start()
        threading.Thread(target=self.__loop_machine).start()

        self.send_to_admin('启动完毕')

    def handler(self, data):
        data = Message(data)
        reply = None

        if data.is_event:
            log.info(data.event_name, title='event')
            self.on_event(data)
            return False

        if data.type:
            filter_result = self.message_filter(data)

            self.message_stack.append({
                'user_id': data.user_id,
                'target_id': data.at_target,
                'group_id': data.group_id,
                'msg_type': data.type,
                'msg_time': int(time.time())
            })

            if data.is_at or data.is_call or data.type == 'friend':
                log.info(
                    f'{("[GID %s]" % data.group_id) if data.group_id else ""}'
                    f'[UID {data.user_id}][{data.nickname}] '
                    f'{data.text_ori}',
                    title='message'
                )

            if type(filter_result) is Chain:
                reply = filter_result

            elif bool(filter_result):
                if data.type == 'group':
                    reply = self.on_group_message(data)
                else:
                    reply = self.on_private_message(data)

        if reply:
            self.send_message(reply)

    @staticmethod
    def restart(delay=3):
        python = sys.executable
        threading.Timer(delay, os.execl, args=(python, python, *sys.argv)).start()

    @abc.abstractmethod
    def message_filter(self, data: Message) -> bool:
        """
        消息过滤函数 \n
        该函数允许返回 Chain 类型的值，返回 Chain 将不会进行消息处理，仅当该函数返回 True 时，才会触发消息处理

        :param data: Message
        :return: bool | Chain
        """
        pass

    @abc.abstractmethod
    def on_private_message(self, data: Message) -> Chain:
        """
        私聊消息处理

        :param data: Message
        :return: Chain
        """
        pass

    @abc.abstractmethod
    def on_group_message(self, data: Message) -> Chain:
        """
        群聊消息处理

        :param data: Message
        :return: Chain
        """
        pass

    @abc.abstractmethod
    def on_event(self, data: Message) -> None:
        """
        事件处理

        :param data: Message
        :return: None
        """
        pass

    @abc.abstractmethod
    def loop_events(self, times: int) -> None:
        """
        循环调用的方法

        :param times: int
        :return:
        """
        pass
