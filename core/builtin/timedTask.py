import asyncio

from typing import *
from core.network import WSOpration
from core.control import StateControl
from core import log

TASK_CORO = Callable[[WSOpration], Coroutine]


class TimedTask:
    def __init__(self, task: TASK_CORO, each: int):
        self.task = task
        self.each = each

    def check(self, t):
        return t >= self.each and t % self.each == 0


class TasksControl:
    timed_tasks: List[TimedTask] = list()

    @classmethod
    def timed_task(cls, each: int = 60):
        """
        注册定时任务
        非严格定时，因为执行协程会产生切换的耗时。所以此注册器定义的循环时间为"约等于"。

        :param each: 循环时间，单位（秒）
        :return:
        """

        def register(task: TASK_CORO):
            cls.timed_tasks.append(TimedTask(task, each))

        return register

    @classmethod
    async def run_tasks(cls, client: WSOpration, step: int = 10):
        try:
            t = 0
            while StateControl.alive:
                await asyncio.sleep(step)

                if not cls.timed_tasks:
                    continue

                t += step
                for task in cls.timed_tasks:
                    if task.check(t):
                        async with log.catch('TimedTask Error:', handler=client.handle_error):
                            await task.task(client)

        except KeyboardInterrupt:
            pass
