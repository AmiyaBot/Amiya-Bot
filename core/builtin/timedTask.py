import asyncio

from typing import *
from core.network import WSOperation
from core.control import StateControl
from core.builtin.messageChain import Chain
from core.help import Helper
from core import log

TASK_CORO = Callable[[], Coroutine[Any, Any, Optional[Chain]]]
CUSTOM_CHECK = Callable[[int], Coroutine[Any, Any, bool]]


class TimedTask:
    def __init__(self, task: TASK_CORO, each: int = None, custom: CUSTOM_CHECK = None):
        self.task = task
        self.each = each
        self.custom = custom

    async def check(self, t) -> bool:
        if self.custom:
            return await self.custom(t)
        if self.each:
            return t >= self.each and t % self.each == 0
        return False


class TasksControl:
    timed_tasks: List[TimedTask] = list()

    @classmethod
    @Helper.record
    def timed_task(cls, each: int = None, custom: CUSTOM_CHECK = None):
        """
        注册定时任务
        非严格定时，因为执行协程会产生切换的耗时。所以此注册器定义的循环时间为"约等于"。

        :param each:   循环执行间隔时间，单位（秒）
        :param custom: 自定义循环规则
        :return:
        """

        def register(task: TASK_CORO):
            cls.timed_tasks.append(TimedTask(task, each, custom))

        return register

    @classmethod
    async def run_tasks(cls, client: WSOperation, step: int = 1):
        try:
            t = 0
            while StateControl.alive:
                await asyncio.sleep(step)

                if not cls.timed_tasks:
                    continue

                t += step
                for task in cls.timed_tasks:
                    if await task.check(t):
                        async with log.catch('TimedTask Error:', handler=client.handle_error):
                            chain = await task.task()
                            if chain:
                                await client.send_message(chain)

        except KeyboardInterrupt:
            pass
