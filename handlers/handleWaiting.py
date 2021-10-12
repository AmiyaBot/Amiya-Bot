import re

from core import Message

from handlers.functions import FunctionIndexes


def waiting_event(func):
    def handler(cls: FunctionIndexes, data: Message):
        wait = data.user_info.waiting
        if wait:
            if 'Recruit' in wait and data.image:
                return cls.arknights.Recruit.action(data)

            if 'Enemy' in wait:
                r = re.search(r'(\d+)', data.text)
                if r:
                    index = int(r.group(1))
                    if index:
                        return cls.arknights.Enemy.find_enemy_by_index(data, index, wait.split('#')[-1])

        return func(cls, data)

    return handler
