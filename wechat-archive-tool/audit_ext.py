import os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

base = r'D:\Work\wechat-article-archive\articles\articles'

issues = {"remote_img_src": 0, "remote_bg_url": 0, "remote_font": 0, "remote_audio": 0, "remote_video_src": 0}

for d in sorted(os.listdir(base)):
    path = os.path.join(base, d, 'index.html')
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()

    # Only check body content area
    body_start = c.find('js_article')
    if body_start < 0:
        body_start = c.find('js_content')
    body = c[body_start:] if body_start > 0 else c

    # 1. img src still remote
    imgs = re.findall(r'<img[^>]*src="(https?://[^"]+)"', body)
    if imgs:
        issues["remote_img_src"] += 1
        if issues["remote_img_src"] <= 3:
            print(f'REMOTE IMG: {d} ({len(imgs)} urls)')
            for u in imgs[:3]:
                print(f'  {u[:100]}')

    # 2. CSS background-image still remote
    bgs = re.findall(r'background-image:\s*url\("?(https?://[^")]+)"?\)', body)
    if bgs:
        issues["remote_bg_url"] += 1
        if issues["remote_bg_url"] <= 3:
            print(f'REMOTE BG: {d} ({len(bgs)} urls)')

    # 3. @font-face with remote src
    fonts = re.findall(r'@font-face[^}]+url\("?(https?://[^")]+)"?\)', body)
    if fonts:
        issues["remote_font"] += 1
        if issues["remote_font"] <= 3:
            print(f'REMOTE FONT: {d}')

    # 4. Audio with remote src
    audio = re.findall(r'<audio[^>]*src="(https?://[^"]+)"', body)
    if audio:
        issues["remote_audio"] += 1
        if issues["remote_audio"] <= 3:
            print(f'REMOTE AUDIO: {d}')

    # 5. Video with remote src
    video = re.findall(r'<video[^>]*src="(https?://[^"]+)"', body)
    if video:
        issues["remote_video_src"] += 1
        if issues["remote_video_src"] <= 3:
            print(f'REMOTE VIDEO: {d}')

print(f'\n=== Summary ===')
print(f'Remote img src: {issues["remote_img_src"]} articles')
print(f'Remote CSS bg: {issues["remote_bg_url"]} articles')
print(f'Remote fonts: {issues["remote_font"]} articles')
print(f'Remote audio: {issues["remote_audio"]} articles')
print(f'Remote video: {issues["remote_video_src"]} articles')
