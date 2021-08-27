import os
import queue
import threading
import traceback
import contextlib

from core.util import log

StopEvent = object()


class ThreadPool:
    def __init__(self, max_thread_num: int = min(32, (os.cpu_count() or 1) + 4), max_task_num: int = 0):

        self.queue = queue.Queue(max_task_num)
        self.max_thread_num = max_thread_num
        self.cancel = False
        self.terminal = False
        self.thread_running_list = []
        self.thread_free_list = []

    def put(self, func, args, callback=None):
        if self.cancel:
            return
        if len(self.thread_free_list) == 0 and len(self.thread_running_list) < self.max_thread_num:
            self.create_thread()

        self.queue.put(
            (func, args, callback)
        )

    def create_thread(self):
        t = threading.Thread(target=self.call)
        t.start()

    def call(self):
        current_thread = threading.currentThread().getName()

        self.thread_running_list.append(current_thread)

        event = self.queue.get()

        while event != StopEvent:
            func, arguments, callback = event

            # noinspection PyBroadException
            try:
                result = func(arguments)
                success = True
            except Exception:
                result = traceback.format_exc()
                success = False
                log.error(result)

            if callback is not None:
                # noinspection PyBroadException
                try:
                    callback(success, result)
                except Exception:
                    log.error(traceback.format_exc())

            with self.worker_state(self.thread_free_list, current_thread):
                if self.terminal:
                    event = StopEvent
                else:
                    event = self.queue.get()
        else:
            self.thread_running_list.remove(current_thread)

    def close(self):
        self.cancel = True

        size = len(self.thread_running_list)
        while size:
            self.queue.put(StopEvent)
            size -= 1

    def terminate(self):
        self.cancel = True
        self.terminal = True

        while self.thread_running_list:
            self.queue.put(StopEvent)

    @contextlib.contextmanager
    def worker_state(self, state_list, worker_thread):
        state_list.append(worker_thread)
        try:
            yield
        finally:
            state_list.remove(worker_thread)
