from typing import *

from core.network import WSOpration
from core.builtin.message import Message, Event, Verify, WaitEvent, wait_events
from core.builtin.messageChain import Chain
from core.database.messages import MessageStack
from core.database.group import GroupActive
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
        group_active: GroupActive = GroupActive.get_or_none(group_id=data.group_id)
        if group_active and group_active.active == 0:
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


async def message_handler(data: Union[Message, Event], opration: WSOpration):
    if type(data) is Message:
        info(str(data))

        MessageStack.insert(data)

        if config.test.enable and data.type == 'group' and data.group_id not in config.test.group:
            return

        if data.user.black == 1:
            return

        waitting: Optional[WaitEvent] = None

        if data.user_id in wait_events:
            waitting = wait_events[data.user_id]

        if waitting and waitting.force:
            waitting.set(data)
            return

        handlers = {
            'temp': BotHandlers.temp_message_handlers,
            'group': BotHandlers.group_message_handlers,
            'friend': BotHandlers.private_message_handlers,
        }
        choice: CHOICE = None

        if BotHandlers.message_middleware:
            data = await BotHandlers.message_middleware(data) or data

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

            reply: Chain = await handler.action(data)
            if reply:
                await opration.send(reply)
                if waitting:
                    waitting.cancel()

        if waitting:
            waitting.set(data)

    elif issubclass(data.__class__, Event):
        info(f'Event: {data}')

        if data.event_name in BotHandlers.event_handlers:
            for handler in BotHandlers.event_handlers[data.event_name]:
                reply: Chain = await handler(data)
                if reply:
                    await opration.send(reply)
