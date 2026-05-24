import re
import asyncio


EXTRACT_JS = """
() => {
    function decode(s) {
        var txt = document.createElement('textarea');
        txt.innerHTML = s;
        return txt.value;
    }
    var scripts = document.querySelectorAll('script');
    for (var i = 0; i < scripts.length; i++) {
        var t = scripts[i].textContent || '';
        if (t.indexOf('publish_page') >= 0 && t.indexOf('total_count') >= 0) {
            try {
                var fn = new Function(t + '; return publish_page;');
                var raw = fn();
                var result = {page_total: 0, publish_count: 0, articles: [], deleted_skipped: 0, non_mass_skipped: 0};
                var list = raw.publish_list || [];
                for (var j = 0; j < list.length; j++) {
                    result.page_total++;
                    var pt = list[j].publish_type;
                    if (pt < 100) { result.non_mass_skipped++; continue; }
                    var decoded = decode(list[j].publish_info);
                    var pi = JSON.parse(decoded);
                    var articles = pi.appmsg_info || [];
                    result.publish_count++;
                    for (var k = 0; k < articles.length; k++) {
                        var a = articles[k];
                        if (!a.title || !a.content_url) continue;
                        if (a.is_deleted) { result.deleted_skipped++; continue; }
                        result.articles.push({
                            title: a.title,
                            link: a.content_url,
                            cover: a.cover || '',
                            create_time: (pi.sent_info && pi.sent_info.time) || 0,
                        });
                    }
                }
                return JSON.parse(JSON.stringify(result));
            } catch(e) {
                return {page_total: 0, publish_count: 0, articles: []};
            }
        }
    }
    return {page_total: 0, publish_count: 0, articles: []};
}
"""


class ArticleScraper:
    def __init__(self, page, config):
        self.page = page
        self.config = config
        self.token = None

    async def run(self):
        self._extract_token()
        await self._navigate_to_account()
        articles, publish_count = await self._fetch_published_articles()
        print(f"[OK] {publish_count} publishes, {len(articles)} articles")
        return articles

    def _extract_token(self):
        m = re.search(r'token=(\d+)', self.page.url)
        if m:
            self.token = m.group(1)

    async def _navigate_to_account(self):
        name = self.config.target_account
        current_url = self.page.url
        if "fakeid=" in current_url or "cgi-bin/home" in current_url:
            return
        print(f"[*] Looking for account: {name}")
        try:
            link = self.page.locator(f"a:has-text('{name}')").first
            await link.wait_for(timeout=15000)
            await link.click()
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            print(f"[OK] Entered account: {name}")
        except Exception as e:
            print(f"[!] Could not navigate to account '{name}': {e}")
            raise

    async def _fetch_published_articles(self):
        all_articles = []
        seen_urls = set()
        publish_count = 0
        total = 0
        begin = 0
        page_size = 20

        while True:
            url = (
                f"https://mp.weixin.qq.com/cgi-bin/appmsgpublish"
                f"?sub=list&begin={begin}&count={page_size}"
                f"&token={self.token}&lang=zh_CN"
            )

            if begin == 0 or begin % 100 == 0:
                print(f"[*] Loading page at offset {begin}...")
            await self.page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(1)

            data = await self.page.evaluate(EXTRACT_JS)
            items = data.get("articles", [])

            if total == 0:
                total = await self.page.evaluate("""
                    () => {
                        var scripts = document.querySelectorAll('script');
                        for (var i = 0; i < scripts.length; i++) {
                            var t = scripts[i].textContent || '';
                            if (t.indexOf('publish_page') >= 0 && t.indexOf('total_count') >= 0) {
                                try {
                                    var fn = new Function(t + '; return publish_page;');
                                    return fn().total_count;
                                } catch(e) { return 0; }
                            }
                        }
                        return 0;
                    }
                """)
                print(f"[*] Total publishes: {total}")

            this_page_total = data.get("page_total", 0)
            this_page_mass = data.get("publish_count", 0)
            publish_count += this_page_mass

            if begin == 0:
                ds = data.get("deleted_skipped", 0)
                nm = data.get("non_mass_skipped", 0)
                if ds or nm:
                    print(f"[*] (First page: {ds} deleted skipped, {nm} non-mass skipped)")

            for item in items:
                link = item.get("link", "")
                if link and link not in seen_urls:
                    seen_urls.add(link)
                    all_articles.append(item)

            if self.config.max_articles > 0 and len(all_articles) >= self.config.max_articles:
                all_articles = all_articles[:self.config.max_articles]
                break

            if this_page_total < page_size:
                break

            begin += page_size
            if begin >= total:
                break

        return all_articles, publish_count
