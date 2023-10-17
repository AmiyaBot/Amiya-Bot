import os
import asyncio

from functools import partial
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(min(32, (os.cpu_count() or 1) + 4))


async def run_in_thread_pool(block_func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, partial(block_func, *args, **kwargs))
