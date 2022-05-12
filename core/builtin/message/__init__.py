import re
import time
import asyncio
import collections

from typing import *
from core.network import WSOperation
from core.database.user import User

equal = collections.namedtuple('equal', ['content'])  # 全等对象，接受一个字符串，表示消息文本完全匹配该值


class Verify:
    def __init__(self, result: bool, weight: Union[int, float] = 0, keywords: List[str] = None):
        """
        消息校验结果对象

        :param result:   校验结果
        :param weight:   权重（优先级），用于当同时存在多个检验结果时，可根据权值匹配优先的结果
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
    def __init__(self, message=None, operation: WSOperation = None):
        """
        消息的处理接口类

        type 只允许赋值为 'friend'（好友消息）、'group'（群组消息）或 'temp'（临时聊天）

        :param message:  原消息对象
        :param operation: Websocket 操作接口
        """
        self.operation = operation
        self.message = message

        self.type = None
        self.message_id = None

        self.face = []
        self.image = []

        self.text = ''
        self.text_digits = ''
        self.text_origin = ''
        self.text_initial = ''
        self.text_cut = []
        self.text_cut_pinyin = []

        self.at_target = []

        self.is_at = False
        self.is_call = False
        self.is_admin = False
        self.is_group_admin = False
        self.is_new_user = False

        self.user_id = None
        self.group_id = None
        self.nickname = None
        self.raw_chain = None

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
        await self.operation.send_message(reply)

    async def waiting(self, reply=None, max_time: int = 30, force: bool = False, target: str = 'user'):
        if target == 'group':
            target_id = self.group_id
        else:
            if self.group_id:
                target_id = f'{self.group_id}_{self.user_id}'
            else:
                target_id = self.user_id

        wid = await wait_events.set_wait(target_id, force, target)

        if reply:
            await self.operation.send_message(reply)

        while max_time:
            await asyncio.sleep(0.5)

            if target_id in wait_events:

                wait_object = wait_events[target_id]

                if wid != wait_object.wid:
                    raise WaitEventCancel(target_id)

                if wait_object.data:
                    data = wait_object.data
                    del wait_events[target_id]
                    return data

            else:
                return None

            max_time -= 0.5

        if wid == wait_events[target_id].wid:
            del wait_events[target_id]


class MessageMatch:
    @staticmethod
    def check_str(data: Message, text: str, level: int) -> Tuple[bool, int, List[str]]:
        if text.lower() in data.text_origin.lower():
            return True, level or 1, [str(text)]
        return False, 0, []

    @staticmethod
    def check_equal(data: Message, text: equal, level: int) -> Tuple[bool, int, List[str]]:
        if text.content == data.text_origin:
            return True, level or 10000, [str(text)]
        return False, 0, []

    @staticmethod
    def check_reg(data: Message, reg: re.Pattern, level: int) -> Tuple[bool, int, List[str]]:
        r = re.search(reg, data.text_origin)
        if r:
            return True, level or (r.re.groups or 1), [str(item) for item in r.groups()]
        return False, 0, []


class Event:
    def __init__(self, event_name, data):
        """
        事件处理

        :param event_name: 事件名
        :param data:       事件数据
        """
        self.event_name = event_name
        self.data = data

    def __str__(self):
        return self.event_name

    def __repr__(self):
        return f'<Event, {self.event_name}>'

    def handle(self, *args, **kwargs):
        pass


class WaitEvent:
    def __init__(self, wid: int, target_id: int, force: bool, target: str):
        self.wid = wid
        self.force = force
        self.target = target
        self.target_id = target_id
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

    async def set_wait(self, target_id: Union[int, str], force: bool, target: str):
        wid = await self.__get_id()

        self.bucket[target_id] = WaitEvent(wid, target_id, force, target)

        return wid


class WaitEventCancel(Exception):
    def __init__(self, key: Union[int, str]):
        self.key = key
        del wait_events[key]

    def __str__(self):
        return f'WaitEventCancel: {self.key}'


wait_events = WaitEventsBucket()
