from typing import *

from core import log
from core.bot import BotHandlers, Handler
from core.control import SpeedControl
from core.network import WSOpration
from core.builtin.message import Message, Event, Verify, wait_events
from core.builtin.messageChain import Chain
from core.database.messages import MessageStack
from core.database.bot import FunctionUsed, DisabledFunction
from core.config import config

speed = SpeedControl(config.speedSetting.maxsize,
                     config.speedSetting.mintime)

CHOICE = Optional[Tuple[Verify, Handler]]


async def choice_handlers(data: Message, handlers: List[Handler]) -> CHOICE:
    candidate: List[Tuple[Verify, Handler]] = []
    disabled: List[str] = []

    if data.group_id:
        query: List[DisabledFunction] = DisabledFunction.select().where(DisabledFunction.group_id == data.group_id,
                                                                        DisabledFunction.status == 1)
        disabled = [item.function_id for item in query]

    for item in handlers:
        if item.function_id in disabled:
            continue

        check = await item.verify(data)
        if check:
            candidate.append((check, item))

    if not candidate:
        return None

    return sorted(candidate, key=lambda n: len(n[0]), reverse=True)[0]


async def message_handler(data: Union[Message, Event], opration: WSOpration):
    if type(data) is Message:
        log.info(str(data))

        MessageStack.insert(data)

        handlers = {
            'temp': BotHandlers.temp_message_handlers,
            'group': BotHandlers.group_message_handlers,
            'friend': BotHandlers.private_message_handlers,
        }
        choice: CHOICE = None

        if data.type in handlers.keys():
            choice = await choice_handlers(data, handlers[data.type])

        if choice:
            handler = choice[1]
            data.verify = choice[0]

            exceed = speed.check_user(data.user_id)

            if exceed == 1:
                if BotHandlers.overspeed_handler:
                    reply: Chain = await BotHandlers.overspeed_handler(data)
                    if reply:
                        await opration.send(reply)
                return
            elif exceed == 2:
                return

            if handler.function_id:
                FunctionUsed \
                    .insert(function_id=handler.function_id) \
                    .on_conflict(conflict_target=[FunctionUsed.function_id],
                                 update={FunctionUsed.use_num: FunctionUsed.use_num + 1}) \
                    .execute()

            reply: Chain = await handler.function(data)
            if reply:
                await opration.send(reply)
        else:
            if data.user_id in wait_events:
                wait_events[data.user_id].data = data

    elif issubclass(data.__class__, Event):
        log.info(f'Event: {data}')

        if data.event_name in BotHandlers.event_handlers:
            for handler in BotHandlers.event_handlers[data.event_name]:
                reply: Chain = await handler(data)
                if reply:
                    await opration.send(reply)
