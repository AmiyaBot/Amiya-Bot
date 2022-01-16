import time
import asyncio

from typing import List, Dict
from core import log


class StateControl:
    alive = True
    keep_running = True

    @classmethod
    def start(cls):
        cls.alive = True

    @classmethod
    def shutdown(cls):
        cls.alive = False
        log.info('waiting all tasks shutdown...')

    @classmethod
    def close(cls):
        cls.shutdown()
        cls.keep_running = False


class SpeedNodes:
    def __init__(self, maxsize: int, mintime: int):
        self.maxsize = maxsize
        self.mintime = mintime
        self.overflow = False
        self.list: List[float] = []

    def __repr__(self):
        return str(self.list)

    def __put(self, t: float):
        if len(self.list) >= self.maxsize:
            self.list.pop(0)
        self.list.append(t)
        self.overflow = False

    def exceed(self, put: bool = True) -> int:
        if len(self.list) >= self.maxsize:
            last = self.list[0]
            curr = time.time()
            if curr - last <= self.mintime:
                if self.overflow:
                    return 2  # 状态2：已超限

                self.overflow = True
                return 1  # 状态1：当前达到限制

        if put:
            self.__put(time.time())

        return 0  # 状态0：未超限


class SpeedControl:
    def __init__(self, maxsize: int, mintime: int):
        self.maxsize = maxsize
        self.mintime = mintime
        self.container: Dict[int, SpeedNodes] = {}

    def __repr__(self):
        return str(self.container)

    async def clean_container(self):
        try:
            while StateControl.alive:
                await asyncio.sleep(self.mintime)
                clean = []
                for user_id, item in self.container.items():
                    if item.exceed(put=False) == 0:
                        clean.append(user_id)

                for user_id in clean:
                    del self.container[user_id]
        except KeyboardInterrupt:
            pass

    def check_user(self, user_id: int):
        """
        检查是否超限

        :param user_id: 用户ID
        :return: 0 - 未超限，1 - 当前达到限制，2 - 已超限
        """
        if user_id not in self.container:
            self.container[user_id] = SpeedNodes(self.maxsize, self.mintime)

        return self.container[user_id].exceed()
