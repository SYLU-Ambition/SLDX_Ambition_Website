#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.browser import BrowserManager
from src.scraper import ArticleScraper
from src.downloader import ArticleDownloader


async def main():
    config = Config()

    browser = BrowserManager(config)
    try:
        await browser.start()
        await browser.ensure_login()

        scraper = ArticleScraper(browser.page, config)
        articles = await scraper.run()

        if not articles:
            print("[!] No articles found!")
            return

        downloader = ArticleDownloader(browser.page, config)
        await downloader.download_all(articles)

        print("\n" + "=" * 60)
        print(f"[OK] All done! Downloaded {len(articles)} articles.")
        print(f"[*] Open {config.output_dir}/browse.html to browse offline.")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n[*] Interrupted by user")
    except Exception as e:
        print(f"\n[X] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
