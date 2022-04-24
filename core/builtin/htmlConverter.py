import os
import json

from typing import Optional, Union
from playwright.async_api import Browser, Page, Playwright, async_playwright
from core.util import Singleton, argv
from core import log

debug = argv('debug')


class PageController:
    def __init__(self, page: Page):
        self.page = page

    async def init_data(self, data: Union[dict, list]):
        await self.page.evaluate(f'init({json.dumps(data)})')

    async def make_image(self):
        return await self.page.screenshot(full_page=True)

    async def close(self):
        await self.page.close()


class ChromiumBrowser(metaclass=Singleton):
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None

    async def launch(self, **kwargs):
        log.info('launching chromium...')

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=not debug, **kwargs)

        log.info('chromium launched successful.')

    async def close(self):
        log.info('closing chromium.')
        await self.browser.close()
        await self.playwright.stop()

    async def open_page(self, url: str, is_file: bool = False):
        if self.browser:
            page = await self.browser.new_page(no_viewport=True)

            if is_file:
                url = 'file:///' + os.path.abspath(url)

            await page.goto(url)
            await page.wait_for_load_state()

            return PageController(page)
