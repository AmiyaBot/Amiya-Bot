import re

from typing import *
from core.builtin.message import Message, MessageMatch, Event, Verify, equal
from core.builtin.timedTask import TasksControl
from core.builtin.messageChain import Chain
from core.help import Helper

CORO = Coroutine[Any, Any, Optional[Chain]]
PREFIX = Union[bool, List[str]]
KEYWORDS = Union[str, equal, re.Pattern, List[Union[str, equal, re.Pattern]]]
FUNC_CORO = Callable[[Message], CORO]
EVENT_CORO = Callable[[Event], CORO]
AFTER_CORO = Callable[[Chain], Coroutine]
BEFORE_CORO = Callable[[Message], Coroutine[Any, Any, bool]]
VERIFY_CORO = Callable[[Message], Coroutine[Any, Any, Union[bool, Tuple[bool, int], Tuple[bool, int, List[str]]]]]
MIDDLE_WARE = Callable[[Message], Coroutine[Any, Any, Optional[Message]]]


class Handler:
    def __init__(self,
                 function_id: str,
                 function: FUNC_CORO,
                 keywords: KEYWORDS = None,
                 custom_verify: VERIFY_CORO = None,
                 check_prefix: PREFIX = True,
                 level: int = 0):
        """
        处理器对象
        将注册到功能候选列表的功能处理器，提供给消息处理器（message_handler）筛选出功能轮候列表。
        不必主动实例化本类，请使用注册器注册功能函数。
        示例：
        @bot.on_group_message(function_id='hello', keywords='你好')
        async def my_function(data: Message):
            ...

        :param function_id:   功能ID
        :param function:      功能函数
        :param keywords:      内置校验方法的关键字，支持字符串、正则、全等句（equal）或由它们构成的列表
        :param custom_verify: 自定义校验方法
        :param check_prefix:  是否校验前缀或指定需要校验的前缀
        :param level:         关键字校验成功后函数的候选默认等级
        """
        self.function_id = function_id
        self.function = function
        self.keywords = keywords
        self.custom_verify = custom_verify
        self.check_prefix = check_prefix
        self.level = level

    def __repr__(self):
        return f'<Handler, {self.function_id}, {self.custom_verify or self.keywords}>'

    def __check(self, data: Message, obj: KEYWORDS) -> Verify:
        methods = {
            str: MessageMatch.check_str,
            equal: MessageMatch.check_equal,
            re.Pattern: MessageMatch.check_reg
        }
        t = type(obj)

        if t in methods.keys():
            method = methods[t]
            check = Verify(*method(data, obj, self.level))
            if check:
                return check

        elif t is list:
            for item in obj:
                check = self.__check(data, item)
                if check:
                    return check

        return Verify(False)

    async def verify(self, data: Message):
        # 检查是否包含前缀触发词，包括 @
        flag = False
        if self.check_prefix:
            if data.is_at:
                flag = True
            else:
                for word in (self.check_prefix if type(self.check_prefix) is list else BotHandlers.prefix_keywords):
                    if data.text_origin.startswith(word):
                        flag = True
                        break

        # 若不包含前缀触发词，且关键字不为全等句式（equal）
        # 则允许当关键字为列表时，筛选列表内的全等句式继续执行校验
        if self.check_prefix and not flag and not type(self.keywords) is equal:
            equal_filter = [n for n in self.keywords if type(n) is equal] if type(self.keywords) is list else []
            if equal_filter:
                self.keywords = equal_filter
            else:
                return Verify(False)

        # 执行自定义校验并修正其返回值
        if self.custom_verify:
            result = await self.custom_verify(data)

            if type(result) is bool or result is None:
                result = result, int(bool(result)), []

            elif type(result) is tuple:
                contrast = result[0], int(result[0]), []
                result = (result + contrast[len(result):])[:3]

            return Verify(*result)

        return self.__check(data, self.keywords)

    async def action(self, data: Message):
        return await self.function(data)


class BotHandlers:
    prefix_keywords: List[str] = list()

    private_message_handlers: List[Handler] = list()
    group_message_handlers: List[Handler] = list()
    temp_message_handlers: List[Handler] = list()
    event_handlers: Dict[str, List[EVENT_CORO]] = dict()
    before_reply_handlers: List[BEFORE_CORO] = list()
    after_reply_handlers: List[AFTER_CORO] = list()

    overspeed_handler: Optional[FUNC_CORO] = None
    message_handler_middleware: Optional[MIDDLE_WARE] = None

    @classmethod
    def detail(cls):
        return [
            f'- private_message_handlers ({len(cls.private_message_handlers)})',
            f'- group_message_handlers ({len(cls.group_message_handlers)})',
            f'- temp_message_handlers ({len(cls.temp_message_handlers)})',
            f'- event_handlers ({len(cls.event_handlers)})',
            f'- timed_tasks ({len(TasksControl.timed_tasks)})'
        ]

    @classmethod
    def add_prefix(cls, words: Union[str, List[str]]):
        """
        添加前缀触发词，在存在前缀触发词的情况下，handlers 会默认检查前缀

        :param words: 触发词，允许为一个触发词列表
        :return:
        """
        if type(words) is str:
            words = [words]
        cls.prefix_keywords += words

    @classmethod
    def handler_register(cls,
                         handlers: List[Handler],
                         function_id: str,
                         keywords: KEYWORDS = None,
                         verify: VERIFY_CORO = None,
                         check_prefix: PREFIX = True,
                         level: int = 0):
        """
        功能注册器工厂函数

        :param function_id:   功能ID
        :param handlers:      注册目标
        :param keywords:      触发关键字
        :param verify:        自定义校验方法
        :param check_prefix:  是否校验前缀或指定需要校验的前缀
        :param level:         关键字校验成功后函数的候选默认等级
        :return:              注册函数的装饰器
        """

        def register(func: FUNC_CORO):
            _handler = Handler(function_id,
                               func,
                               level=level,
                               check_prefix=check_prefix)

            if verify:
                _handler.custom_verify = verify
            else:
                _handler.keywords = keywords

            handlers.append(_handler)

        return register

    @classmethod
    @Helper.record
    def on_private_message(cls,
                           function_id: str = None,
                           keywords: KEYWORDS = None,
                           verify: VERIFY_CORO = None,
                           check_prefix: PREFIX = False,
                           level: int = 0):
        """
        注册一个私聊消息的功能
        功能函数接受一个 Message 参数，内含消息的内容以及回复等操作，允许返回一个 Chain 对象进行回复

        :param function_id:   功能ID，不唯一，仅用于记录该功能的使用数量
        :param keywords:      触发关键字，支持字符串、正则、全等句（equal）或由它们构成的列表
        :param verify:        自定义校验方法，当该参数被赋值时，keywords 将会失效
        :param check_prefix:  是否校验前缀或指定需要校验的前缀
        :param level:         关键字校验成功后函数的候选默认等级
        :return:              功能注册器工厂函数
        """
        return cls.handler_register(cls.private_message_handlers,
                                    function_id,
                                    keywords,
                                    verify,
                                    check_prefix,
                                    level)

    @classmethod
    @Helper.record
    def on_group_message(cls,
                         function_id: str = None,
                         keywords: KEYWORDS = None,
                         verify: VERIFY_CORO = None,
                         check_prefix: PREFIX = True,
                         level: int = 0):
        """
        注册一个群组消息的功能
        功能函数接受一个 Message 参数，内含消息的内容以及回复等操作，允许返回一个 Chain 对象进行回复

        :param function_id:   功能ID，不唯一，仅用于记录该功能的使用数量
        :param keywords:      触发关键字，支持字符串、正则、全等句（equal）或由它们构成的列表
        :param verify:        自定义校验方法，当该参数被赋值时，keywords 将会失效
        :param check_prefix:  是否校验前缀或指定需要校验的前缀
        :param level:         关键字校验成功后函数的候选默认等级
        :return:              功能注册器工厂函数
        """
        return cls.handler_register(cls.group_message_handlers,
                                    function_id,
                                    keywords,
                                    verify,
                                    check_prefix,
                                    level)

    @classmethod
    @Helper.record
    def on_temp_message(cls,
                        function_id: str = None,
                        keywords: KEYWORDS = None,
                        verify: VERIFY_CORO = None,
                        check_prefix: PREFIX = True,
                        level: int = 0):
        """
        注册一个临时聊天的功能
        功能函数接受一个 Message 参数，内含消息的内容以及回复等操作，允许返回一个 Chain 对象进行回复

        :param function_id:   功能ID，不唯一，仅用于记录该功能的使用数量
        :param keywords:      触发关键字，支持字符串、正则、全等句（equal）或由它们构成的列表
        :param verify:        自定义校验方法，当该参数被赋值时，keywords 将会失效
        :param check_prefix:  是否校验前缀或指定需要校验的前缀
        :param level:         关键字校验成功后函数的候选默认等级
        :return:              功能注册器工厂函数
        """
        return cls.handler_register(cls.temp_message_handlers,
                                    function_id,
                                    keywords,
                                    verify,
                                    check_prefix,
                                    level)

    @classmethod
    @Helper.record
    def on_event(cls, events: Union[List[Any], Any]):
        """
        事件处理注册器工厂函数
        处理函数接受一个 Event 参数，内含事件的内容，允许返回一个 Chain 对象进行消息发送

        注意：同一个事件名能拥有多个处理函数，这是出于灵活处理考虑，在注册时请避免冲突的操作

        :param events: 监听的事件，可传入 MiraiEvents 的属性类或事件名的字符串，以及以上的列表
        :return:       注册函数的装饰器
        """

        def handler(func: EVENT_CORO):
            nonlocal events

            if type(events) is not list:
                events = [events]

            for event in events:
                if issubclass(event, Event):
                    event_name = event.__name__
                else:
                    if type(event) is str:
                        event_name = event
                    else:
                        raise TypeError('Event must be property of MiraiEvents or string of event name.')

                if event_name not in cls.event_handlers:
                    cls.event_handlers[event_name] = []

                cls.event_handlers[event_name].append(func)

        return handler

    @classmethod
    def on_overspeed(cls, handler: FUNC_CORO):
        """
        处理触发消息速度限制的事件，只允许存在一个

        :param handler: 处理函数
        :return:
        """
        if not cls.overspeed_handler:
            cls.overspeed_handler = handler
        else:
            raise Exception('Only one overspeed handler can exist.')

    @classmethod
    def before_bot_reply(cls, handler: BEFORE_CORO):
        """
        Bot 回复前处理，用于定义当 Bot 即将回复消息时的操作，该操作会在处理消息前执行

        :param handler: 处理函数
        :return:
        """
        cls.before_reply_handlers.append(handler)

    @classmethod
    def after_bot_reply(cls, handler: AFTER_CORO):
        """
        Bot 回复后处理，用于定义当 Bot 回复消息后的操作，该操作会在发送消息后执行

        :param handler: 处理函数
        :return:
        """
        cls.after_reply_handlers.append(handler)

    @classmethod
    def handler_middleware(cls, handler: MIDDLE_WARE):
        """
        Message 对象与消息处理器的中间件，用于对 Message 作进一步的客制化处理，只允许存在一个

        :param handler: 处理函数
        :return:
        """
        if not cls.message_handler_middleware:
            cls.message_handler_middleware = handler
        else:
            raise Exception('Only one message middleware can exist.')


on_private_message = BotHandlers.on_private_message
on_group_message = BotHandlers.on_group_message
on_temp_message = BotHandlers.on_temp_message
on_event = BotHandlers.on_event
on_overspeed = BotHandlers.on_overspeed
before_bot_reply = BotHandlers.before_bot_reply
after_bot_reply = BotHandlers.after_bot_reply
handler_middleware = BotHandlers.handler_middleware
timed_task = TasksControl.timed_task
