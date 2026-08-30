#!/usr/bin/env python3
"""
Optimize WeChat article archive for GitHub Pages deployment.

Steps:
1. CSS Deduplication (extract shared styles)
2. Font Deduplication
3. Emoji Deduplication
4. Image compression (resize + quality, backup originals)
5. HTML minification
6. Generate metadata JSON for VitePress
"""

import os, re, hashlib, shutil, json, subprocess
from collections import defaultdict
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
ARTICLES = PROJ / 'doc/public/wechat/articles'
SHARED = ARTICLES / '_shared'
BACKUP = PROJ / 'doc/wechat-backups'
METADATA_JSON = PROJ / 'doc/public/wechat/wechat-metadata.json'
MIN_COVERAGE = 0.8
MAX_WIDTH = 1200
JPEG_QUALITY = 75

def get_html_files():
    return sorted(ARTICLES.glob('*/index.html'))

# ─── Step 1: CSS Deduplication ───────────────────────────────────────

def analyze_and_extract_css(html_files):
    block_counts = defaultdict(int)
    block_sample = {}
    print(f"Analyzing {len(html_files)} HTML files...")
    for fp in html_files:
        html = fp.read_text()
        blocks = re.findall(r'<style[^>]*>.*?</style>', html, re.DOTALL)
        seen = set()
        for b in blocks:
            h = hashlib.md5(b.encode()).hexdigest()
            if h not in seen:
                block_counts[h] += 1
                block_sample[h] = b
                seen.add(h)
    threshold = int(len(html_files) * MIN_COVERAGE)
    common = sorted(
        [(h, cnt, block_sample[h]) for h, cnt in block_counts.items() if cnt >= threshold],
        key=lambda x: -len(x[2])
    )
    print(f"Found {len(common)} common CSS blocks (≥{threshold}/{len(html_files)} files)")
    SHARED.mkdir(parents=True, exist_ok=True)
    css_map = {}
    for idx, (h, cnt, block) in enumerate(common):
        inner = re.sub(r'</?style[^>]*>', '', block).strip()
        fname = f's{idx:03d}.css'
        (SHARED / fname).write_text(inner)
        css_map[h] = fname
        print(f"  {fname}: {len(inner):,} bytes ({cnt} files)")
    block_map = {h: block_sample[h] for h, cnt, _ in common}
    return css_map, block_map

def rewrite_html(html_files, css_map, block_content):
    print("Rewriting HTML files...")
    saved = 0
    for i, fp in enumerate(html_files):
        html = fp.read_text()
        orig = len(html)
        for h in css_map:
            html = html.replace(block_content[h], f'<link rel="stylesheet" href="../_shared/{css_map[h]}">')
        if orig != len(html):
            fp.write_text(html)
            saved += orig - len(html)
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(html_files)}...")
    print(f"  Done. Saved {saved / 1e6:.1f} MB")

# ─── Step 2: Font Deduplication ──────────────────────────────────────

def dedup_fonts(html_files):
    ttf_files = list(ARTICLES.glob('*/font_*.ttf'))
    if not ttf_files:
        return
    font_dir = SHARED / 'fonts'
    font_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ttf_files[0], font_dir / 'wechat.ttf')
    for fp in html_files:
        rel = os.path.relpath(str(font_dir), str(fp.parent))
        html = fp.read_text()
        html = re.sub(r'url\([^)]*\.ttf\)', f'url({rel}/wechat.ttf)', html)
        fp.write_text(html)
    for fp in ttf_files:
        if fp.parent != font_dir:
            fp.unlink()
    print(f"Deduplicated {len(ttf_files)} fonts → 1 shared")

# ─── Step 3: Emoji Deduplication ─────────────────────────────────────

def dedup_emojis():
    emoji_map = {}
    removed = 0
    for fp in sorted(ARTICLES.glob('*/emoji_*.png')):
        content = fp.read_bytes()
        h = hashlib.md5(content).hexdigest()
        if h in emoji_map:
            fp.unlink()
            removed += 1
        else:
            emoji_map[h] = fp
    print(f"Removed {removed} duplicate emoji PNGs, kept {len(emoji_map)} unique")

# ─── Step 4: Image Compression ───────────────────────────────────────

def _compress_one(args):
    """Compress a single image file. Returns (before, after, action)."""
    fp, = args
    from PIL import Image
    size_before = fp.stat().st_size
    if size_before < 5120:
        return (size_before, size_before, 'skip')

    try:
        img = Image.open(fp)
        w, h = img.size
        if w > MAX_WIDTH:
            ratio = MAX_WIDTH / w
            img = img.resize((MAX_WIDTH, int(h * ratio)), Image.LANCZOS)

        ext = fp.suffix.lower()
        if ext in ('.jpg', '.jpeg'):
            if img.mode in ('RGBA', 'P', 'CMYK'):
                img = img.convert('RGB')
            img.save(str(fp), 'JPEG', quality=JPEG_QUALITY, optimize=True)
        elif ext == '.png':
            img.save(str(fp), 'PNG', optimize=True)
        else:
            return (size_before, size_before, 'skip')

        size_after = fp.stat().st_size
        return (size_before, size_after, 'ok')
    except Exception as e:
        return (size_before, size_before, f'err: {e}')

def compress_images():
    """Resize large images, compress JPEGs, backup originals using multiprocessing."""
    image_files = []
    for pat in ('*/cover.*', '*/img_*.*', '*/bg_*.*'):
        image_files.extend(ARTICLES.glob(pat))
    if not image_files:
        return

    try:
        from PIL import Image
    except ImportError:
        print("Pillow not available, trying jpegoptim fallback...")
        try:
            subprocess.run(['jpegoptim', '--version'], capture_output=True)
            jpegs = [f for f in image_files if f.suffix.lower() in ('.jpg', '.jpeg')]
            for fp in jpegs:
                subprocess.run(['jpegoptim', '--strip-all', '--max=85', str(fp)],
                              capture_output=True, timeout=10)
            print(f"  Compressed {len(jpegs)} JPEGs with jpegoptim")
            return
        except (FileNotFoundError, Exception):
            print("Neither Pillow nor jpegoptim available, skipping image compression")
            return

    print(f"Compressing {len(image_files)} images with Pillow...")

    # Backup originals first
    BACKUP.mkdir(parents=True, exist_ok=True)
    img_backup = BACKUP / 'images'
    img_backup.mkdir(parents=True, exist_ok=True)
    for fp in image_files:
        rel_path = fp.relative_to(ARTICLES)
        backup_path = img_backup / rel_path
        if not backup_path.exists():
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(fp), str(backup_path))

    # Compress with multiprocessing
    try:
        from multiprocessing import Pool
        with Pool() as pool:
            results = pool.map(_compress_one, [(fp,) for fp in image_files])
    except Exception as ex:
        print(f"  Multiprocessing failed ({ex}), falling back to serial...")
        results = [_compress_one((fp,)) for fp in image_files]

    total_before = sum(r[0] for r in results)
    total_after = sum(r[1] for r in results)
    compressed = sum(1 for r in results if r[2] == 'ok')
    skipped = sum(1 for r in results if r[2] == 'skip')
    errors = sum(1 for r in results if r[2].startswith('err'))

    reduction = total_before - total_after
    print(f"  Compressed {compressed} images, skipped {skipped}, errors {errors}")
    print(f"  Before: {total_before / 1e6:.1f} MB → After: {total_after / 1e6:.1f} MB")
    print(f"  Saved: {reduction / 1e6:.1f} MB ({100 * reduction / max(total_before, 1):.1f}%)")
    print(f"  Originals backed up to: {img_backup}")

def _compress_one_generic(args):
    """Compress a single image file (for generic dirs). Returns (before, after, action)."""
    from PIL import Image
    fp, = args
    fp = Path(fp)
    size_before = fp.stat().st_size
    if size_before < 5120:
        return (size_before, size_before, 'skip')

    try:
        img = Image.open(fp)
        w, h = img.size
        if w > MAX_WIDTH:
            ratio = MAX_WIDTH / w
            img = img.resize((MAX_WIDTH, int(h * ratio)), Image.LANCZOS)

        ext = fp.suffix.lower()
        if ext in ('.jpg', '.jpeg'):
            if img.mode in ('RGBA', 'P', 'CMYK'):
                img = img.convert('RGB')
            img.save(str(fp), 'JPEG', quality=JPEG_QUALITY, optimize=True)
        elif ext in ('.png', '.webp'):
            img.save(str(fp), 'PNG', optimize=True) if ext == '.png' else img.save(str(fp), 'WEBP', quality=JPEG_QUALITY, optimize=True)
        else:
            return (size_before, size_before, 'skip')

        size_after = fp.stat().st_size
        return (size_before, size_after, 'ok')
    except Exception as e:
        return (size_before, size_before, f'err: {e}')


def compress_dir_images(root_dir, backup_subdir):
    """Recursively compress all images under a generic directory (e.g. Photo/).

    Backs up originals to doc/wechat-backups/<backup_subdir>/ (one copy only,
    so re-running is idempotent: already-backed-up files are left untouched).
    """
    root_dir = Path(root_dir)
    if not root_dir.is_dir():
        print(f"  [skip] {root_dir} does not exist")
        return
    # Exclude images under the backup dir (in case the backup lives inside root_dir)
    backup_root = Path(BACKUP).resolve()
    image_files = []
    for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
        for fp in root_dir.rglob(ext):
            if backup_root != root_dir.resolve() and backup_root in fp.resolve().parents:
                continue  # skip files already in a backup directory
            image_files.append(fp)
    if not image_files:
        print(f"  [skip] {root_dir}: no images")
        return

    # Backup originals once (idempotent). Determine which files are NEW
    # (i.e. had no backup before this run) so we only compress those.
    img_backup = BACKUP / backup_subdir
    new_files = []
    for fp in image_files:
        rel = fp.relative_to(root_dir)
        bkp = img_backup / rel
        if bkp.exists():
            continue  # already backed up -> compressed before, leave alone
        bkp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(fp), str(bkp))
        new_files.append(fp)

    if not new_files:
        print(f"  [{backup_subdir}] all {len(image_files)} images already compressed (idempotent)")
        return

    print(f"  Compressing {len(new_files)} images in {root_dir.name} (backup: {backup_subdir})...")
    try:
        from multiprocessing import Pool
        with Pool() as pool:
            results = pool.map(_compress_one_generic, [(str(fp),) for fp in new_files])
    except Exception as ex:
        print(f"    Multiprocessing failed ({ex}), falling back to serial...")
        results = [_compress_one_generic((str(fp),)) for fp in new_files]

    total_before = sum(r[0] for r in results)
    total_after = sum(r[1] for r in results)
    ok = sum(1 for r in results if r[2] == 'ok')
    err = sum(1 for r in results if r[2].startswith('err'))
    reduction = total_before - total_after
    print(f"    {root_dir.name}: {ok} compressed, {err} errors")
    print(f"    Before: {total_before / 1e6:.1f} MB → After: {total_after / 1e6:.1f} MB  (Saved {reduction / 1e6:.1f} MB / {100 * reduction / max(total_before, 1):.1f}%)")


# ─── Step 5: HTML Minification ───────────────────────────────────────

def minify_html():
    """Remove excessive whitespace from HTML files."""
    print("Minifying HTML...")
    saved = 0
    html_files = list(ARTICLES.glob('*/index.html'))
    for fp in html_files:
        html = fp.read_text()
        orig = len(html)
        # Collapse multiple whitespace (but not in <pre> or <code>)
        parts = re.split(r'(<pre[^>]*>.*?</pre>|<code[^>]*>.*?</code>)', html, flags=re.DOTALL)
        result = []
        for part in parts:
            if part.startswith('<pre') or part.startswith('<code'):
                result.append(part)
            else:
                part = re.sub(r'\n\s*\n', '\n', part)
                part = re.sub(r'>\s+<', '><', part)
                result.append(part)
        html = ''.join(result)
        fp.write_text(html)
        saved += orig - len(html)
    print(f"  Saved {saved / 1e6:.1f} MB")

# ─── Step 6: Generate Metadata JSON ──────────────────────────────────

def decode_html_entities(s):
    """Decode common HTML entities back to their literal characters."""
    if not s:
        return s
    return (s.replace('&amp;', '&')
             .replace('&lt;', '<')
             .replace('&gt;', '>')
             .replace('&quot;', '"')
             .replace('&#x27;', "'")
             .replace('&nbsp;', ' '))


def generate_metadata():
    """Generate metadata JSON for VitePress data loader."""
    print("Generating metadata...")
    SKIP = ['2026-05-22_公众号运营回归个人通知', '2025-09-15_我们搬家啦', '2025-06-03_沈理电协Ambition战队官网发布', '2025-06-18_大疆_2026_校招', '2024-06-13_大疆_2025', '2024-07-04_DJI_大疆', '2024-07-07_测一测你来_DJI', '2022-04-25_下一场，去大疆', '2018-04-13_DJI大疆创新RoboMaster机器人夏令营', '2018-03-09_RoboMaster2018最全招聘']
    articles = []
    for entry_dir in sorted(ARTICLES.iterdir()):
        if not entry_dir.is_dir() or entry_dir.name.startswith('_'):
            continue
        if any(entry_dir.name.startswith(s) for s in SKIP):
            continue
        title_part = entry_dir.name[11:]
        if title_part.startswith('转载') or title_part.startswith('转载_'):
            continue
        if any(entry_dir.name.startswith(s) for s in SKIP):
            continue
        m = re.match(r'^(\d{4}-\d{2}-\d{2})_(.*)', entry_dir.name)
        if not m:
            continue
        date_str, _ = m.groups()
        html_path = entry_dir / 'index.html'
        title = entry_dir.name[11:].replace('_', ' ')
        if html_path.exists():
            content = html_path.read_text()
            tm = re.search(r'<title>(.*?)</title>', content)
            if tm:
                title = decode_html_entities(tm.group(1).strip())

        has_cover = False
        cover_ext = None
        for ext in ('jpg', 'png', 'webp'):
            if (entry_dir / f'cover.{ext}').exists():
                has_cover = True
                cover_ext = ext
                break

        articles.append({
            'date': date_str,
            'year': int(date_str[:4]),
            'title': title,
            'dir': entry_dir.name,
            'hasCover': has_cover,
            'coverExt': cover_ext
        })

    articles.sort(key=lambda a: a['date'], reverse=True)
    METADATA_JSON.write_text(json.dumps(articles, ensure_ascii=False))
    print(f"  Generated metadata for {len(articles)} articles → {METADATA_JSON}")
    return articles

# ─── Stats ───────────────────────────────────────────────────────────

def show_stats():
    total = sum(f.stat().st_size for f in ARTICLES.rglob('*') if f.is_file())
    print(f"\nFinal articles size: {total / 1e6:.1f} MB")

# ─── Main ────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("WeChat Article Archive Optimizer")
    print("=" * 60)

    html_files = get_html_files()
    print(f"\nFound {len(html_files)} article HTML files\n")

    # Step 1: CSS Dedup
    print("[1/6] CSS Deduplication")
    css_map, block_content = analyze_and_extract_css(html_files)
    rewrite_html(html_files, css_map, block_content)

    # Step 2: Font Dedup
    print("\n[2/6] Font Deduplication")
    dedup_fonts(html_files)

    # Step 3: Emoji Dedup
    print("\n[3/6] Emoji Deduplication")
    dedup_emojis()

    # Step 4: Image Compression
    print("\n[4/6] Image Compression (wechat articles)")
    compress_images()

    # Step 4b: Compress other large public image dirs to keep Pages < 1 GB
    print("\n[4b] Compress public gallery dirs")
    for root, sub in (
        ('doc/public/Photo', 'photo_images'),
        ('doc/public/Ambition_Introduction', 'ambition_intro_images'),
        ('doc/public/Knowledge', 'knowledge_images'),
        ('doc/public/History', 'history_images'),
    ):
        compress_dir_images(PROJ / root, sub)

    # Step 5: HTML Minification
    print("\n[5/6] HTML Minification")
    minify_html()

    # Step 6: Metadata
    print("\n[6/6] Generate Metadata")
    generate_metadata()

    print("\n" + "=" * 60)
    show_stats()

if __name__ == '__main__':
    main()
