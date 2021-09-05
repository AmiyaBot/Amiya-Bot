from core import Message

from handlers.functions import FunctionIndexes


def waiting_event(func):
    def handler(cls: FunctionIndexes, data: Message):
        wait = data.user_info.waiting
        if wait:
            if wait == 'Recruit' and data.image:
                return cls.arknights.Recruit.action(data)

        return func(cls, data)

    return handler
