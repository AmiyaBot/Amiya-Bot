from typing import *

from core.network import WSOperation
from core.builtin.message import Message, Event, Verify, WaitEvent, wait_events
from core.builtin.messageChain import Chain
from core.database.messages import MessageStack
from core.database.group import check_group_active
from core.database.bot import FunctionUsed, DisabledFunction
from core.control import SpeedControl
from core.config import config
from core.util import read_yaml
from core.bot import BotHandlers, Handler
from core.log import info

bot_conf = read_yaml('config/private/bot.yaml')
speed = SpeedControl(bot_conf.speedSetting.maxsize,
                     bot_conf.speedSetting.mintime)

CHOICE = Optional[Tuple[Verify, Handler]]


async def choice_handlers(data: Message, handlers: List[Handler]) -> CHOICE:
    candidate: List[Tuple[Verify, Handler]] = []
    disabled: List[str] = []
    active = True

    if data.group_id:
        if not check_group_active(data.group_id):
            active = False

        query: List[DisabledFunction] = DisabledFunction.select().where(DisabledFunction.group_id == data.group_id,
                                                                        DisabledFunction.status == 1)
        disabled = [item.function_id for item in query]

    for item in handlers:
        if item.function_id in disabled or (not active and item.function_id != 'admin'):
            continue

        check = await item.verify(data)
        if check:
            candidate.append((check, item))

    if not candidate:
        return None

    return sorted(candidate, key=lambda n: len(n[0]), reverse=True)[0]


async def message_handler(data: Union[Message, Event], operation: WSOperation):
    if type(data) is Message:

        is_test = config.test.enable and data.type == 'group' and data.group_id not in config.test.group
        is_black = data.user.black == 1

        if not is_test:
            info(str(data))  # 输出日志

        # 检查封测和黑名单人员
        if is_test or is_black:
            MessageStack.insert(data)
            return

        # 执行中间处理函数
        if BotHandlers.message_handler_middleware:
            data = await BotHandlers.message_handler_middleware(data) or data

        waiting: Optional[WaitEvent] = None
        if data.group_id:
            waiting_target = f'{data.group_id}_{data.user_id}'
        else:
            waiting_target = data.user_id

        # 寻找是否存在等待事件
        if data.group_id in wait_events:
            waiting = wait_events[data.group_id]
        if waiting_target in wait_events:
            waiting = wait_events[waiting_target]

        # 若存在等待事件并且等待事件设置了强制等待，则直接进入事件
        if waiting and waiting.force:
            waiting.set(data)
            MessageStack.insert(data, True)
            return

        handlers = {
            'temp': BotHandlers.temp_message_handlers,
            'group': BotHandlers.group_message_handlers,
            'friend': BotHandlers.private_message_handlers,
        }
        choice: CHOICE = None

        # 选择功能
        if data.type in handlers.keys():
            choice = await choice_handlers(data, handlers[data.type])

        MessageStack.insert(data, bool(choice))

        # 执行选中的功能
        if choice:
            handler = choice[1]
            data.verify = choice[0]

            # 检查超限
            exceed = speed.check_user(data.user_id)

            if exceed == 1:
                if BotHandlers.overspeed_handler:
                    reply: Chain = await BotHandlers.overspeed_handler(data)
                    if reply:
                        await operation.send_message(reply)
                return
            elif exceed == 2:
                return

            # 执行前置处理函数
            flag = True
            if BotHandlers.before_reply_handlers:
                for action in BotHandlers.before_reply_handlers:
                    res = await action(data)
                    if not res:
                        flag = False
            if not flag:
                return

            # 记录使用数
            if handler.function_id:
                FunctionUsed.insert_or_update(
                    insert={'function_id': handler.function_id},
                    update={FunctionUsed.use_num: FunctionUsed.use_num + 1},
                    conflict_target=[FunctionUsed.function_id]
                )

            # 执行功能并取消等待
            reply: Chain = await handler.action(data)
            if reply:
                await operation.send_message(reply)
                if waiting:
                    waiting.cancel()

        # 未选中任何功能或功能无法返回时，进入等待事件（若存在）
        if waiting:
            waiting.set(data)

    elif issubclass(data.__class__, Event):
        info(f'Event: {data}')

        if data.event_name in BotHandlers.event_handlers:
            for handler in BotHandlers.event_handlers[data.event_name]:
                reply: Chain = await handler(data)
                if reply:
                    await operation.send_message(reply)
