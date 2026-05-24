import os
import re
import asyncio
import hashlib
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import aiohttp

CONCURRENCY = 5


class ArticleDownloader:
    def __init__(self, page, config):
        self.page = page
        self.config = config
        self.output_dir = config.output_dir
        self.video_dir = os.path.join(self.output_dir, "videos")
        self.downloaded_videos = set()
        self.sem = asyncio.Semaphore(CONCURRENCY)
        self.session = None
        self.ok_count = 0
        self.skip_count = 0
        self.fail_count = 0
        self.articles_for_progress = []
        os.makedirs(self.video_dir, exist_ok=True)

    async def download_all(self, articles):
        self.articles_for_progress = articles
        cookies_dict = {}
        try:
            cookies = await self.page.context.cookies()
            for c in cookies:
                domain = c.get("domain", "") or ""
                if any(d in domain for d in ["weixin", "qq"]):
                    cookies_dict[c["name"]] = c["value"]
        except Exception:
            pass

        self.context = self.page.context

        connector = aiohttp.TCPConnector(limit=CONCURRENCY, force_close=True)
        self.session = aiohttp.ClientSession(
            connector=connector,
            cookies=cookies_dict,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            },
            timeout=aiohttp.ClientTimeout(total=30),
        )

        tasks = []
        for i, article in enumerate(articles):
            tasks.append(self._download_one(article, i, len(articles)))
        await asyncio.gather(*tasks)

        await self.session.close()
        self.session = None

        print(f"\n[Summary] OK={self.ok_count} Skip={self.skip_count} Fail={self.fail_count} Total={len(articles)}")
        await self._generate_index(articles)
        await self._generate_readme()

    async def _download_one(self, article, index, total):
        async with self.sem:
            await self._download_article(article, index, total)

    async def _download_article(self, article, index, total):
        title = article["title"]
        link = article["link"]
        if not link:
            self.fail_count += 1
            return

        timestamp = article.get("create_time", 0)
        date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d") if timestamp else "unknown"

        safe_title = re.sub(r'[<>:"/\\|?*]', "_", title)
        safe_title = re.sub(r"\s+", "_", safe_title)
        safe_title = safe_title[:60].strip("_.")

        article_dir_name = f"{date_str}_{safe_title}"
        article_dir = os.path.join(self.output_dir, "articles", article_dir_name)
        html_path = os.path.join(article_dir, "index.html")

        article["local_dir"] = article_dir_name
        article["local_path"] = f"articles/{article_dir_name}"

        if os.path.exists(html_path):
            self.skip_count += 1
            return

        os.makedirs(article_dir, exist_ok=True)

        html_content = await self._fetch_article_html(link)
        if not html_content or len(html_content) < 500:
            self.fail_count += 1
            return

        soup = BeautifulSoup(html_content, "lxml")
        self._fix_image_urls(soup)
        await self._inline_css(soup)
        self._clean_html(soup)

        await self._download_body_images(soup, article_dir)

        title_tag = soup.find("title")
        if title_tag:
            title_tag.string = title
        else:
            head = soup.find("head")
            if head is not None:
                new_title = soup.new_tag("title")
                new_title.string = title
                head.append(new_title)

        video_info = self._extract_video_info(soup)
        if video_info:
            article["has_video"] = True
            article["video_info"] = video_info

        if self.config.download_videos and video_info:
            await self._download_video(video_info, article_dir)

        for v in video_info:
            local_file = v.get("local_file")
            if not local_file:
                continue
            vid = v["vid"]
            if v["type"] == "direct":
                for tag in soup.find_all("video"):
                    src = tag.get("src", "")
                    if f"vid={vid}" in src or vid in src:
                        tag["src"] = local_file

        with open(html_path, "w", encoding="utf-8") as f:
            html_str = str(soup)
            html_str = html_str.replace("大冲在思考", "沈理电协")
            f.write(html_str)

        cover_local = await self._download_cover(article, article_dir)
        if cover_local:
            article["cover_local"] = cover_local

        self.ok_count += 1
        total_done = self.ok_count + self.skip_count + self.fail_count
        if total_done % 50 == 0:
            print(f"[Progress] {total_done}/{len(self.articles_for_progress)} OK={self.ok_count} Skip={self.skip_count} Fail={self.fail_count}")

    def _expand_swiper_images(self, soup):
        swiper_items = soup.find_all("div", class_="swiper_item")
        if not swiper_items:
            return

        image_urls = []
        for item in swiper_items:
            src = item.get("data-src", "")
            if src and src.startswith("http"):
                image_urls.append(src)
            else:
                img = item.find("img")
                if img:
                    s = img.get("src", "") or img.get("data-src", "")
                    if s and s.startswith("http"):
                        image_urls.append(s)

        if len(image_urls) <= 1:
            return

        desc_el = soup.find("p", id="js_image_desc")
        if not desc_el:
            desc_el = soup.find("p", class_=re.compile("share_notice"))

        if desc_el and desc_el.parent:
            gallery = soup.new_tag("div")
            gallery["style"] = "margin-top:16px;"
            for url in image_urls:
                img_tag = soup.new_tag("img", src=url.split("?")[0])
                img_tag["style"] = "max-width:100%;height:auto;display:block;margin:8px auto;border-radius:4px;"
                img_tag["loading"] = "lazy"
                gallery.append(img_tag)
            desc_el.insert_after(gallery)

    async def _fetch_article_html(self, link):
        page = None
        try:
            page = await self.context.new_page()
            await page.goto(link, wait_until="domcontentloaded", timeout=30000)
            try:
                await page.wait_for_selector(
                    "#js_content, .rich_media_content, #js_article, .share_content_page",
                    state="attached",
                    timeout=10000,
                )
            except Exception:
                pass
            await asyncio.sleep(2)
            try:
                await page.wait_for_selector(
                    ".share_notice, .rich_media_title, .js_video_channel_title, #video_share_global_info",
                    state="attached",
                    timeout=5000,
                )
            except Exception:
                pass
            try:
                await page.wait_for_selector(
                    "video, .mpvideo_wrp video, #js_mpvedio video, .js_video_channel_container video",
                    state="attached",
                    timeout=8000,
                )
            except Exception:
                pass
            html_content = await page.content()
            return html_content
        except asyncio.TimeoutError:
            return None
        except Exception:
            return None
        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass

    async def _inline_css(self, soup):
        head = soup.find("head")
        if head is None:
            return

        link_tags = head.find_all("link", rel="stylesheet")
        for link in link_tags:
            href = link.get("href", "")
            if not href:
                link.decompose()
                continue

            full_url = href
            if href.startswith("//"):
                full_url = "https:" + href
            elif href.startswith("/"):
                full_url = "https://mp.weixin.qq.com" + href

            try:
                async with self.session.get(full_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        css_text = await resp.text(encoding="utf-8", errors="replace")
                        if css_text and len(css_text) > 10:
                            style_tag = soup.new_tag("style")
                            style_tag.string = css_text
                            link.replace_with(style_tag)
                        else:
                            link.decompose()
                    else:
                        link.decompose()
            except Exception:
                link.decompose()

    def _clean_html(self, soup):
        self._expand_swiper_images(soup)

        for script in soup.find_all("script"):
            script.decompose()

        for link in soup.find_all("link"):
            rel = (link.get("rel") or [])[0] if isinstance(link.get("rel"), list) else link.get("rel", "")
            if rel in ("dns-prefetch", "modulepreload", "preload", "prefetch",
                        "apple-touch-icon-precomposed", "shortcut icon", "mask-icon",
                        "stylesheet", "canonical", "alternate"):
                link.decompose()
                continue
            href = link.get("href", "")
            if any(d in href for d in ("res.wx.qq.com", "mmbiz.qpic.cn", "mpcdn.qpic.cn",
                                          "mpcdn.weixin.qq.com", "file.daihuo.qq.com",
                                          "wxa.wxs.qq.com", "open.weixin.qq.com")):
                link.decompose()
                continue
            if "modulepreload" in link.get("as", ""):
                link.decompose()

        for meta in soup.find_all("meta", attrs={"http-equiv": re.compile(r"refresh", re.I)}):
            meta.decompose()

        for el in soup.select("[data-croporisrc],[data-cropsel],[data-ratio]"):
            for attr in ["data-croporisrc", "data-cropsel", "data-ratio"]:
                if attr in el.attrs:
                    del el[attr]

        for span in soup.find_all("span"):
            if not span.get_text(strip=True) and not span.find():
                children = list(span.children)
                if not children or all(isinstance(c, str) and not c.strip() for c in children):
                    span.decompose()

        remove_ids = [
            "js_emotion_panel_pc", "js_profile_card", "js_unlogin_bottom_bar",
            "js_bottom_bar", "js_stream_bottom_bar_area",
            "content_bottom_area", "js_tags_preview_toast",
            "js_temp_bottom_area", "js_font_panel_area",
            "js_a11y_colon", "js_a11y_comma", "js_a11y_period",
            "unlogin_bottom_bar",
            "js_fullscreen_layout_padding", "js_top_ad_area",
            "js_pc_qr_code", "js_analyze_btn",
            "js_minipro_dialog", "js_link_dialog", "js_product_dialog",
            "js_cmt_container", "js_bt_cmt_area", "js_msg_area", "js_bottom_form",
            "js_row_immersive_stream_wrap", "js_row_immersive_cover_img",
            "js_novel_link", "js_novel_cover_old", "js_novel_title_old",
            "js_author_name",
        ]
        for rid in remove_ids:
            for el in soup.find_all(id=rid):
                el.decompose()

        remove_classes = [
            "comment_primary_emotion_panel_wrp", "comment_primary_emotion_panel",
            "weui-dialog__wrp",
            "wx_expand_article",
            "rich_media_area_extra", "rich_media_area_extra_inner",
            "qr_code_pc", "qr_code_pc_img", "qr_code_pc_inner", "qr_code_pc_outer",
            "qrcode-con", "jump_wx_qrcode_desc", "jump_wx_qrcode_img",
            "jump_author_avatar_con",
            "interaction_bar", "interaction_bar__wrap",
            "function_mod", "function_mod_inner", "function_bd",
            "novel-card__link", "novel-card__new-only", "novel-card__old-only",
            "novel-info", "novel-cover-group", "novel-cover",
            "novel-meta", "novel-title", "novel-description", "arrow-jump-icon",
            "analyze_btn_wrap", "close-button", "go-button",
            "outer_dialog", "bottom_bar_placeholder",
            "fullscreen-layout-padding", "fullscreen-layout-padding__content",
            "top_banner", "wx_row_immersive_stream_wrap", "wx_row_immersive_stream_mask",
            "wx_bottom_modal_wrp", "wx_user_profile_dialog_pc",
            "wx_user_friend_profile_dialog", "wx_identity_dialog_pc",
            "underline-container", "stream_comment_dialog", "discuss_more_dialog_wrp",
            "recommend_friend_dialog", "comment_complaint_dialog",
            "discuss_form_input", "discuss_bottom_form", "discuss_form_avatar_wrp",
            "weui-pc-popover__wrp", "weui-mask_transparent",
            "weui-pc-popover", "weui-half-screen-dialog_wrp",
            "reward_area", "like_area",
            "discuss_list_wrp", "fold-show-more", "discuss_container",
            "weui-half-screen-dialog", "wx_bottom_modal",
            "wx_bottom_modal_group_container", "wx_bottom_modal_group",
            "weui-half-screen-dialog__hd__wrp", "weui-half-screen-dialog__hd",
            "weui-half-screen-dialog__bd", "weui-half-screen-dialog__ft",
            "weui-half-screen-dialog__slide-icon",
        ]
        for cls in remove_classes:
            for el in soup.find_all(class_=cls):
                el.decompose()

        for el in soup.select("[id^='js_a11y_']"):
            el.decompose()

        for el in soup.find_all(attrs={"aria-hidden": "true"}):
            el.decompose()

        for el in soup.select('.rich_media_area_extra,[id="content_bottom_area"],'
                             '[class*="qr_code"],[class*="qrcode"],'
                             '[class*="interaction_bar"],[class*="function_mod"],'
                             '[class*="novel-card"],[class*="novel-info"],[class*="novel-cover"],'
                             '[class*="comment_complaint"],[class*="recommend_friend"],'
                             '[class*="stream_comment"],[class*="discuss_more"],'
                             '[class*="discuss_form"],[class*="discuss_bottom"],'
                             '[class*="discuss_container"],[class*="discuss_list"],'
                             '[class*="outer_dialog"],[class*="bottom_bar"]'):
            el.decompose()

        for el in soup.select('div[data-v-23c65d01],div[data-v-50f4b45b],'
                              'div[data-v-769fa6a3],div[data-v-3a6db0ba],'
                              'div[data-v-4a43b332],div[data-v-8e27743c],'
                              'div[data-v-ef645c18],div[data-v-040c297f],'
                              'span[data-v-8e27743c],span[data-v-23c65d01],'
                              'span[data-v-769fa6a3],span[data-v-50f4b45b]'):
            el.decompose()

        for tag in list(soup.descendants):
            try:
                if tag.name == "div" and tag.get("style"):
                    st = tag.get("style", "")
                    if "safe-area-inset" in st and "visibility: hidden" in st:
                        tag.decompose()
            except AttributeError:
                continue

        for el in soup.select('div.wx-root,div.wx_bottom_modal_wrp,'
                              'div.weui-mask,div.weui-half-screen-dialog,'
                              'div.weui-mask_transparent,div.weui-pc-popover__wrp,'
                              '            iframe[src*="open.weixin.qq.com"]'):
            el.decompose()

        head = soup.find("head")
        if head is not None and not head.find("meta", attrs={"name": "viewport"}):
            meta = soup.new_tag("meta", name="viewport", content="width=device-width, initial-scale=1.0")
            head.insert(0, meta)

        if head is not None:
            style = soup.new_tag("style")
            style.string = """#js_content,#js_image_content{visibility:visible!important;opacity:1!important}
#js_novel_card,.novel-card,.novel-card__link,.novel-card__old-only,.novel-info{display:none!important}
.share_media_swiper,.share_media_swiper_size_placeholder,.share_media_swiper_content,.img_swiper_area,.swiper_item,.swiper_item_img{max-width:100%!important}
.swiper_indicator_wrp,.swiper_dot_wrp,.swiper_indicator_wrp_pc,#img_list_indicator{display:none!important}
#img_swiper_placeholder{display:none!important}
.mpvideo_wrp:empty{display:none!important}
.rich_media_area_extra,.rich_media_area_extra_inner,#js_pc_qr_code,.qr_code_pc,.qr_code_pc_outer{display:none!important}
.interaction_bar,.function_mod,.function_mod_inner,.function_bd{display:none!important}
.outer_dialog,.weui-dialog__wrp,.weui-pc-popover__wrp{display:none!important}
.bottom_bar_placeholder{display:none!important}
img{max-width:100%!important;height:auto!important;box-sizing:border-box!important}
body{margin:0;padding:0;background:#fff!important;-webkit-text-size-adjust:100%}
.rich_media_content{overflow:visible!important}
.rich_media{margin:0!important;padding:0!important}
.rich_media_inner{max-width:677px;margin:0 auto;padding:20px 16px}
.rich_media_area_primary{position:static!important}
:root{--new-title-color:rgba(0,0,0,.9);--weui-BG-0:#EDEDED;--weui-BG-1:#F7F7F7;--weui-BG-2:#FFFFFF;--weui-BG-3:#F7F7F7;--weui-BG-4:#4C4C4C;--weui-BG-5:#FFFFFF;--weui-FG-0:rgba(0,0,0,.9);--weui-FG-HALF:rgba(0,0,0,.9);--weui-FG-1:rgba(0,0,0,.5);--weui-FG-2:rgba(0,0,0,.3);--weui-FG-3:rgba(0,0,0,.1);--weui-FG-4:rgba(0,0,0,.15);--weui-RED:#FA5151;--weui-ORANGE:#FA9D3B;--weui-YELLOW:#FFC300;--weui-GREEN:#91D300;--weui-LIGHTGREEN:#95EC69;--weui-BRAND:#07C160;--weui-BLUE:#10AEFF;--weui-INDIGO:#1485EE;--weui-PURPLE:#6467F0;--weui-WHITE:#FFFFFF;--weui-LINK:#576B95;--weui-TEXTGREEN:#06AE56;--weui-FG:#000;--weui-BG:#FFFFFF;--weui-TAG-TEXT-ORANGE:#FA9D3B;--weui-TAG-BACKGROUND-ORANGE:rgba(250,157,59,.1);--weui-TAG-TEXT-GREEN:#06AE56;--weui-TAG-BACKGROUND-GREEN:rgba(6,174,86,.1);--weui-TAG-TEXT-BLUE:#10AEFF;--weui-TAG-BACKGROUND-BLUE:rgba(16,174,255,.1);--weui-TAG-TEXT-BLACK:rgba(0,0,0,.5);--weui-TAG-BACKGROUND-BLACK:rgba(0,0,0,.05);--weui-BTN-DISABLED-FONT-COLOR:rgba(0,0,0,.2);--weui-BTN-DEFAULT-BG:#F2F2F2;--weui-BTN-DEFAULT-COLOR:#06AE56;--weui-BTN-DEFAULT-ACTIVE-BG:#E6E6E6;--weui-DIALOG-LINE-COLOR:rgba(0,0,0,.1);--weui-BG-COLOR-ACTIVE:#ECECEC;--weui-GLYPH-WHITE-0:rgba(255,255,255,.8);--weui-GLYPH-WHITE-1:rgba(255,255,255,.5);--weui-GLYPH-WHITE-2:rgba(255,255,255,.3);--weui-GLYPH-WHITE-3:#FFFFFF}"""
            head.append(style)

    def _extract_video_info(self, soup):
        video_info = []
        for mv in soup.find_all("mpvideo"):
            vid = mv.get("vid") or mv.get("data-vid")
            if vid:
                video_info.append({
                    "type": "mpvideo",
                    "vid": vid,
                    "url": f"https://v.qq.com/x/page/{vid}.html",
                    "download_method": "yt-dlp",
                })
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "")
            if "v.qq.com" in src:
                vid = parse_qs(urlparse(src).query).get("vid", [None])[0]
                if vid:
                    video_info.append({
                        "type": "iframe",
                        "vid": vid,
                        "url": f"https://v.qq.com/x/page/{vid}.html",
                        "download_method": "yt-dlp",
                    })
        for tag in soup.find_all("video"):
            src = tag.get("src", "")
            vid = None
            if "vid=" in src:
                m = re.search(r'vid=([^&]+)', src)
                if m:
                    vid = m.group(1)
            if (src.startswith("http") and "mpvideo.qpic.cn" in src) or vid:
                vid = vid or hashlib.md5(src.encode()).hexdigest()[:16]
                video_info.append({
                    "type": "direct",
                    "vid": vid,
                    "url": src,
                    "download_method": "direct",
                })
        return video_info

    def _fix_image_urls(self, soup):
        for img in soup.find_all("img"):
            data_src = img.get("data-src", "")
            src = img.get("src", "")
            real_src = data_src or src

            if real_src and real_src.startswith("//"):
                real_src = "https:" + real_src

            if real_src and "mmbiz.qpic.cn" in real_src:
                img["src"] = real_src
            elif real_src:
                img["src"] = real_src

            for attr in ["data-src", "data-type", "data-ratio", "data-w", "data-croporisrc",
                         "data-cropsel", "data-backh", "data-backw", "data-copyright"]:
                if attr in img.attrs:
                    del img[attr]

            if "data-original-style" in img.attrs:
                img["style"] = img["data-original-style"]
                del img["data-original-style"]

            if "style" in img.attrs:
                st = img["style"]
                if "width" in st and "max-width" not in st:
                    img["style"] = st.strip().rstrip(";") + "; max-width: 100%; height: auto; box-sizing: border-box"

        for tag in soup.find_all(style=True):
            style_val = tag.get("style", "")
            if "url(//" in style_val:
                tag["style"] = re.sub(
                    r"url\(\s*(//[^)]+)\s*\)",
                    r"url(https:\1)",
                    style_val,
                )
            if "url(//" in tag.get("style", ""):
                tag["style"] = re.sub(
                    r"url\(\s*(//[^)]+)\s*\)",
                    r"url(https:\1)",
                    tag["style"],
                )

    async def _download_body_images(self, soup, article_dir):
        downloaded = {}
        idx = 0

        for img in soup.find_all("img"):
            src = img.get("src", "")
            if not src.startswith("http"):
                continue
            if "mmbiz.qpic.cn" not in src and "mpcdn" not in src:
                continue

            if src in downloaded:
                img["src"] = downloaded[src]
                continue

            base_url = src.split("?")[0]
            ext = base_url.rsplit(".", 1)[-1].lower()
            if ext not in ("jpg", "jpeg", "png", "gif", "webp", "bmp"):
                ext = "jpg"

            try:
                async with self.session.get(src, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        if len(data) > 500:
                            idx += 1
                            local_name = f"img_{idx}.{ext}"
                            local_path = os.path.join(article_dir, local_name)
                            with open(local_path, "wb") as fh:
                                fh.write(data)
                            img["src"] = local_name
                            downloaded[src] = local_name
            except Exception:
                pass

        bg_urls = set()
        for tag in soup.find_all(style=True):
            style_val = tag.get("style", "")
            for m in re.finditer(r'background-image:\s*url\(["\']?(https?://[^"\')]+(?:mmbiz\.qpic\.cn|mpcdn)[^"\')]*)["\']?\)', style_val):
                bg_urls.add(m.group(1))

        for url in bg_urls:
            if url in downloaded:
                continue
            try:
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        if len(data) > 500:
                            idx += 1
                            ext = url.split("?")[0].rsplit(".", 1)[-1].lower()
                            if ext not in ("jpg", "jpeg", "png", "gif", "webp"):
                                ext = "jpg"
                            local_name = f"bg_{idx}.{ext}"
                            local_path = os.path.join(article_dir, local_name)
                            with open(local_path, "wb") as fh:
                                fh.write(data)
                            downloaded[url] = local_name
            except Exception:
                pass

        if downloaded:
            for tag in soup.find_all(style=True):
                style_val = tag.get("style", "")
                for url, local_name in downloaded.items():
                    style_val = style_val.replace(url, local_name)
                tag["style"] = style_val

    async def _download_cover(self, article, article_dir):
        cover_url = article.get("cover", "")
        if not cover_url:
            return None
        if cover_url.startswith("//"):
            cover_url = "https:" + cover_url
        try:
            async with self.session.get(cover_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    ct = resp.headers.get("Content-Type", "")
                    ext = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif", "image/webp": "webp"}.get(ct.split(";")[0], "jpg")
                    data = await resp.read()
                    if len(data) > 1000:
                        cover_path = os.path.join(article_dir, f"cover.{ext}")
                        with open(cover_path, "wb") as f:
                            f.write(data)
                        return f"cover.{ext}"
        except Exception:
            pass
        return None

    async def _download_video(self, video_info, article_dir):
        for v in video_info:
            vid = v["vid"]
            if vid in self.downloaded_videos:
                continue
            method = v.get("download_method", "yt-dlp")

            if method == "direct":
                local_name = f"video_{vid}.mp4"
                local_path = os.path.join(article_dir, local_name)
                try:
                    async with self.session.get(v["url"],
                                                  timeout=aiohttp.ClientTimeout(total=300)) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            if len(data) > 1024:
                                with open(local_path, "wb") as fh:
                                    fh.write(data)
                                size_mb = len(data) / 1e6
                                print(f"  [Video] Downloaded {local_name} ({size_mb:.1f}MB)")
                                self.downloaded_videos.add(vid)
                                v["local_file"] = local_name
                except asyncio.TimeoutError:
                    print(f"  [Video] Timeout downloading {local_name}, skipping")
                except Exception as e:
                    print(f"  [Video] Failed to download {local_name}: {e}")
                continue

            output_template = os.path.join(article_dir, f"video_{vid}.%(ext)s")
            try:
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp",
                    "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--merge-output-format", "mp4",
                    "-o", output_template, "--no-playlist",
                    "--quiet", "--no-warnings",
                    v["url"],
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                if proc.returncode == 0:
                    self.downloaded_videos.add(vid)
                    v["local_file"] = f"video_{vid}.mp4"
                else:
                    proc2 = await asyncio.create_subprocess_exec(
                        "yt-dlp", "-o", output_template, "--no-playlist",
                        "--quiet", "--no-warnings", v["url"],
                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                    )
                    await proc2.communicate()
                    if proc2.returncode == 0:
                        self.downloaded_videos.add(vid)
                        v["local_file"] = f"video_{vid}.mp4"
            except FileNotFoundError:
                print("  [Video] yt-dlp not found, skipping video download")
                return
            except Exception as e:
                print(f"  [Video] yt-dlp failed for {v['vid']}: {e}")

    async def _generate_index(self, articles):
        index_path = os.path.join(self.output_dir, "browse.html")
        articles.sort(key=lambda a: a.get("create_time", 0), reverse=True)

        years = {}
        for a in articles:
            ts = a.get("create_time", 0)
            year = datetime.fromtimestamp(ts).year if ts else 0
            if year not in years:
                years[year] = []
            years[year].append(a)

        items_html = ""
        for year in sorted(years.keys(), reverse=True):
            items_html += f'<div class="year-title">{year}</div>'
            for a in years[year]:
                title = a["title"]
                ts = a.get("create_time", 0)
                date_str = datetime.fromtimestamp(ts).strftime("%m-%d") if ts else "???"
                local_path = a.get("local_path", "")
                link = a.get("link", "")
                cover_local = a.get("cover_local", "")
                has_video = a.get("has_video", False)

                local_href = f"{local_path}/index.html" if local_path else link
                cover_img = ""
                if cover_local and local_path:
                    cover_img = f'<div class="cv"><img src="{local_path}/{cover_local}" loading="lazy"></div>'
                vb = ' <span class="vb">VIDEO</span>' if has_video else ""

                items_html += f"""
<li>{cover_img}<a href="{local_href}" target="_blank" class="t">{title}{vb}</a><span class="m">{date_str}</span></li>"""

        html = f"""<!DOCTYPE html>
<html lang=zh-CN>
<meta charset=UTF-8>
<meta name=viewport content="width=device-width,initial-scale=1.0">
<title>沈理电协 - 文章存档</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;max-width:880px;margin:0 auto;padding:20px;background:#fafafa;color:#333;line-height:1.6}}
.header{{text-align:center;padding:32px 0 8px}}
.header h1{{font-size:1.8em;font-weight:700;color:#1a1a2e}}
.header p{{color:#888;font-size:.9em;margin-top:4px}}
.site-link{{text-align:center;margin:4px 0 20px}}
.site-link a{{font-size:.85em;color:#576b95;text-decoration:none;border-bottom:1px dashed #576b95}}
.site-link a:hover{{color:#07c160;border-color:#07c160}}
.year-title{{font-size:1.15em;font-weight:600;color:#1a1a2e;padding:16px 0 8px;border-bottom:2px solid #e8e8e8;margin-bottom:4px;margin-top:8px}}
ul{{list-style:none}}
li{{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:6px;transition:background .15s;border-bottom:1px solid #f0f0f0}}
li:hover{{background:#f0f5ff}}
.cv{{flex-shrink:0;width:90px;height:60px;overflow:hidden;border-radius:4px;background:#eee}}
.cv img{{width:100%;height:100%;object-fit:cover}}
.t{{flex:1;min-width:0;font-size:.95em;color:#3a3a3a;text-decoration:none;font-weight:500;line-height:1.4;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.t:hover{{color:#07c160}}
.m{{flex-shrink:0;font-size:.82em;color:#aaa;font-family:monospace}}
.vb{{flex-shrink:0;display:inline-block;background:#e74c3c;color:#fff;font-size:.65em;padding:1px 5px;border-radius:3px;vertical-align:middle;margin-left:4px}}
@media(max-width:600px){{body{{padding:10px}}li{{padding:8px 10px;gap:8px}}.cv{{width:70px;height:48px}}h1{{font-size:1.3em}}.t{{font-size:.85em}}}}
</style>
<div class=header>
<h1>沈理电协</h1>
<p>共 {len(articles)} 篇文章 - 存档于 {datetime.now().strftime("%Y-%m-%d")}</p>
</div>
<div class=site-link>
<a href="/wechat">访问官网存档页面（VitePress 版）</a>
</div>
<ul>{items_html}</ul>"""

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[OK] Index page: {index_path}")

    async def _generate_readme(self):
        readme_path = os.path.join(self.output_dir, "README.md")
        content = "# 文章存档\n\n打开 `browse.html` 浏览所有文章。\n\n- 已嵌入响应式样式\n- 已移除阻塞脚本和无关UI元素\n- 含缩略图预览\n- 视频已本地化保存\n"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)
