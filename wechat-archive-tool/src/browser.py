import json
import os
import asyncio
from playwright.async_api import async_playwright

COOKIE_FILE = "wechat_cookies.json"


class BrowserManager:
    def __init__(self, config):
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        await self._load_cookies()
        self.page = await self.context.new_page()

    async def stop(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _load_cookies(self):
        if os.path.exists(COOKIE_FILE):
            try:
                with open(COOKIE_FILE, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                if cookies:
                    await self.context.add_cookies(cookies)
            except Exception as e:
                print(f"[!] Failed to load cookies: {e}")

    async def save_cookies(self):
        cookies = await self.context.cookies()
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"[*] Cookies saved")

    async def ensure_login(self):
        await self.page.goto(
            "https://mp.weixin.qq.com/", wait_until="domcontentloaded"
        )
        await asyncio.sleep(2)

        current_url = self.page.url
        if "token=" in current_url:
            print("[OK] Already logged in (valid session)")
            await self.save_cookies()
            return

        print("=" * 60)
        print("  请用微信扫描浏览器窗口中的二维码登录")
        print("  Please scan the QR code with WeChat to log in")
        print("=" * 60)

        try:
            await self.page.wait_for_url(
                lambda url: "token=" in url,
                timeout=self.config.login_timeout_ms,
            )
            print("[OK] Login successful!")
            await self.save_cookies()
        except Exception as e:
            print(f"[X] Login failed or timed out: {e}")
            raise
