import re
import time
import asyncio
import collections

from typing import *
from core.network import WSOpration
from core.database.user import User

equal = collections.namedtuple('equal', ['content'])  # 全等对象，接受一个字符串，表示消息文本完全匹配该值


class Verify:
    def __init__(self, result: bool, weight: Union[int, float] = 0, keywords: List[str] = None):
        """
        消息校验结果对象

        :param result:   校验结果
        :param weight:   权值，用于当同时存在多个检验结果时，可根据权值匹配优先的结果
        :param keywords: 校验成功匹配出来的关键字列表
        """
        self.result = result
        self.keywords = keywords or []
        self.weight = weight

    def __bool__(self):
        return self.result

    def __repr__(self):
        return f'<Verify, {self.result}, {self.weight}>'

    def __len__(self):
        return self.weight


class Message:
    def __init__(self, message=None, opration: WSOpration = None):
        """
        消息的处理接口类

        type 只允许赋值为 'friend'（好友消息）、'group'（群组消息）或 'temp'（临时聊天）

        :param message:  原消息对象
        :param opration: Websocket 操作接口
        """
        self.opration = opration
        self.message = message

        self.type = None
        self.message_id = None

        self.face = []
        self.image = []

        self.text = ''
        self.text_origin = ''
        self.text_digits = ''
        self.text_initial = ''
        self.text_cut = []
        self.text_cut_pinyin = []

        self.at_target = ''

        self.is_at = False
        self.is_call = False
        self.is_admin = False
        self.is_group_admin = False
        self.is_new_user = False

        self.user_id = ''
        self.group_id = ''
        self.nickname = ''
        self.raw_chain = ''

        self.time = int(time.time())

        self.verify: Optional[Verify] = None
        self.user: Optional[User] = None

    def __str__(self):
        text = self.text_origin.replace('\n', ' ')
        face = ''.join([f'[face:{n}]' for n in self.face])
        image = '[image]' * len(self.image)

        return 'Type:{type:7}Group:{group:<12}User:{user:<12}{username}: {message}'.format(
            **{
                'type': self.type,
                'user': self.user_id,
                'group': self.group_id or 'None',
                'username': self.nickname,
                'message': text + face + image
            }
        )

    def __repr__(self):
        return f'<Message, {self.message}>'

    async def send(self, reply):
        await self.opration.send(reply)

    async def waiting(self, reply=None, max_time: int = 30, force: bool = False):
        wid = await wait_events.set_wait(self.user_id, force)

        if reply:
            await self.opration.send(reply)

        while max_time:
            await asyncio.sleep(0.5)

            if self.user_id in wait_events:

                wait_object = wait_events[self.user_id]

                if wid != wait_object.wid:
                    raise WaitEventCancel(self.user_id)

                if wait_object.data:
                    data = wait_object.data
                    del wait_events[self.user_id]
                    return data

            else:
                return None

            max_time -= 0.5

        if wid == wait_events[self.user_id].wid:
            del wait_events[self.user_id]

    async def keep_waiting(self, max_time: int = 30):
        # todo 保持等待，在发送结束指令前，将会无限返回等待消息
        pass


class MessageMatch:
    @staticmethod
    def check_str(data: Message, text: str) -> Tuple[bool, int, List[str]]:
        if text.lower() in data.text.lower():
            return True, 1, [str(text)]
        return False, 0, []

    @staticmethod
    def check_equal(data: Message, text: equal) -> Tuple[bool, int, List[str]]:
        if text.content == data.text:
            return True, 10000, [str(text)]
        return False, 0, []

    @staticmethod
    def check_reg(data: Message, reg: re.Pattern) -> Tuple[bool, int, List[str]]:
        r = re.search(reg, data.text)
        if r:
            return True, r.re.groups or 1, [str(item) for item in r.groups()]
        return False, 0, []


class Event:
    def __init__(self, event_name, event_message):
        """
        事件的处理接口类

        :param event_message: 原消息对象
        """
        self.event_message = event_message
        self.event_name = event_name

    def __str__(self):
        return self.event_name

    def __repr__(self):
        return f'<Event, {self.event_message}>'

    def handle(self, *args, **kwargs):
        pass


class WaitEvent:
    def __init__(self, wid: int, user_id: int, force: bool):
        self.wid = wid
        self.force = force
        self.user_id = user_id
        self.data: Optional[Message] = None

    def set(self, data: Message):
        self.data = data

    def cancel(self):
        self.wid = None


class WaitEventsBucket:
    def __init__(self):
        self.id = 0
        self.lock = asyncio.Lock()
        self.bucket: Dict[Union[int, str], WaitEvent] = {}

    def __contains__(self, item):
        return item in self.bucket

    def __getitem__(self, item):
        try:
            return self.bucket[item]
        except KeyError:
            return None

    def __delitem__(self, key):
        try:
            del self.bucket[key]
        except KeyError:
            pass

    async def __get_id(self):
        async with self.lock:
            self.id += 1
            return self.id

    async def set_wait(self, user_id: Union[int, str], force: bool):
        wid = await self.__get_id()

        self.bucket[user_id] = WaitEvent(wid, user_id, force)

        return wid


class WaitEventCancel(Exception):
    def __init__(self, key: Union[int, str]):
        self.key = key
        del wait_events[key]

    def __str__(self):
        return f'WaitEventCancel: {self.key}'


wait_events = WaitEventsBucket()
