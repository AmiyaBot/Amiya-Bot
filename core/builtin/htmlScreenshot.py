import os

from typing import Optional
from playwright.async_api import Browser, Playwright, async_playwright
from core.util import Singleton
from core import log


class HtmlScreenshot(metaclass=Singleton):
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None

    async def launch(self, **kwargs):
        log.info('launching chromium...')

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False, **kwargs)

        log.info('chromium launched successful.')

    async def close(self):
        log.info('closing chromium.')
        await self.browser.close()
        await self.playwright.stop()

    async def open_page(self, url: str):
        if self.browser:
            page = await self.browser.new_page()

            await page.goto(url)
            await page.wait_for_load_state()

            return page

    async def screenshot(self, url: str, is_file: bool = False):
        if is_file:
            url = 'file:///' + os.path.abspath(url)
        page = await self.open_page(url)
        if page:
            content = await page.screenshot(full_page=True)
            await page.close()

            return content
