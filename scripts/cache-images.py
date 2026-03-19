#!/usr/bin/env python3
"""
Validate and cache article images for CEO Briefing.

For each card in HTML files and each story in category-news JSON:
1. Find og:image from source URLs
2. Validate the image URL (HTTP 200 + image content-type)
3. Download to images/cache/{hash}.{ext}
4. Update HTML data-image and JSON image_url with local cached path

Usage: python3 scripts/cache-images.py
"""
import hashlib, json, mimetypes, os, re, ssl, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = Path('/Users/xand/.openclaw/workspace/ceo-briefing')
CACHE_DIR = BASE / 'images' / 'cache'
TIMEOUT = 6
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

EXT_MAP = {
    'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp',
    'image/gif': '.gif', 'image/svg+xml': '.svg', 'image/avif': '.avif',
}

HTML_FILES = [
    'index.html', 'ja.html',
    'ai-review.html', 'vc-review.html', 'energy-review.html',
    'space-review.html', 'health-wellness-review.html',
    'longevity-review.html', 'sports-entertainment-review.html',
    'ai-review-ja.html', 'vc-review-ja.html', 'energy-review-ja.html',
    'space-review-ja.html', 'health-wellness-review-ja.html',
    'longevity-review-ja.html', 'sports-entertainment-review-ja.html',
]


def fetch_bytes(url, max_bytes=MAX_IMAGE_SIZE):
    """Fetch URL, return (bytes, content_type) or (None, None)."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            if resp.status != 200:
                return None, None
            ct = resp.headers.get('Content-Type', '').split(';')[0].strip().lower()
            data = resp.read(max_bytes + 1)
            if len(data) > max_bytes:
                return None, None
            return data, ct
    except Exception:
        return None, None


def get_og_image(url):
    """Fetch a page and extract og:image URL."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            html = resp.read(50000).decode('utf-8', errors='ignore')
            m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
            if not m:
                m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
            if m and m.group(1).startswith('http'):
                return m.group(1)
    except Exception:
        pass
    return None


def validate_and_cache(image_url):
    """Download image, validate, cache locally. Returns relative path or None."""
    if not image_url or not image_url.startswith('http'):
        return None

    url_hash = hashlib.sha256(image_url.encode()).hexdigest()[:16]

    # Check if already cached
    for cached in CACHE_DIR.glob(f'{url_hash}.*'):
        return f'/images/cache/{cached.name}'

    data, ct = fetch_bytes(image_url)
    if not data or not ct:
        return None

    # Must be an image content-type
    if not ct.startswith('image/'):
        return None

    ext = EXT_MAP.get(ct, '')
    if not ext:
        # Try to guess from URL
        url_ext = os.path.splitext(image_url.split('?')[0])[1].lower()
        if url_ext in ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg', '.avif'):
            ext = url_ext
        else:
            ext = '.jpg'  # default

    filename = f'{url_hash}{ext}'
    filepath = CACHE_DIR / filename
    filepath.write_bytes(data)
    return f'/images/cache/{filename}'


def resolve_image_for_sources(source_urls):
    """Given source URLs, find and cache an og:image."""
    for url in source_urls[:3]:
        if 'fonts.google' in url or not url.startswith('http'):
            continue
        og = get_og_image(url)
        if og:
            cached = validate_and_cache(og)
            if cached:
                return cached
    return None


def process_html_files():
    """Process all HTML files: find cards, resolve images, update data-image."""
    stats = {'processed': 0, 'cached': 0, 'failed': 0}

    for fname in HTML_FILES:
        fpath = BASE / fname
        if not fpath.exists():
            continue

        html = fpath.read_text()
        cards = list(re.finditer(
            r'(<article\s+class="card[^"]*"[^>]*>)(.*?)(</article>)',
            html, re.DOTALL
        ))
        if not cards:
            continue

        tasks = {}
        for i, m in enumerate(cards):
            tag, body = m.group(1), m.group(2)
            # Skip if already has a valid cached image
            existing = re.search(r'data-image="(/images/cache/[^"]+)"', tag)
            if existing:
                continue
            # Also skip if has an existing data-image that's an http URL — we'll try to cache it
            existing_url = re.search(r'data-image="(https?://[^"]+)"', tag)
            if existing_url:
                tasks[i] = {'type': 'direct', 'url': existing_url.group(1)}
                continue
            # Extract source URLs from card
            urls = [u for u in re.findall(r'href=["\']([^"\']+)["\']', body)
                    if u.startswith('http') and 'fonts.google' not in u]
            if urls:
                tasks[i] = {'type': 'source', 'urls': urls}

        if not tasks:
            continue

        print(f'  {fname}: {len(tasks)} cards need images...')

        results = {}
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {}
            for idx, task in tasks.items():
                if task['type'] == 'direct':
                    futures[pool.submit(validate_and_cache, task['url'])] = idx
                else:
                    futures[pool.submit(resolve_image_for_sources, task['urls'])] = idx
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    result = fut.result()
                    if result:
                        results[idx] = result
                except Exception:
                    pass

        if not results:
            stats['failed'] += len(tasks)
            continue

        stats['cached'] += len(results)
        stats['failed'] += len(tasks) - len(results)

        # Update HTML (backwards to preserve offsets)
        new_html = html
        for i in sorted(results.keys(), reverse=True):
            m = cards[i]
            old_tag = m.group(1)
            cached_path = results[i]
            if 'data-image=' in old_tag:
                new_tag = re.sub(r'data-image="[^"]*"', f'data-image="{cached_path}"', old_tag)
            else:
                new_tag = old_tag.replace('>', f' data-image="{cached_path}">', 1)
            new_html = new_html[:m.start(1)] + new_tag + new_html[m.end(1):]

        fpath.write_text(new_html)
        stats['processed'] += 1
        print(f'  ✅ {fname}: cached {len(results)} images')

    return stats


def process_category_news():
    """Process category-news JSON files: resolve and cache images."""
    stats = {'cached': 0, 'failed': 0}

    for jname in ['category-news.json', 'category-news-ja.json']:
        jpath = BASE / 'data' / jname
        if not jpath.exists():
            continue

        data = json.loads(jpath.read_text())
        categories = data.get('categoryNews', [])
        modified = False

        tasks = []
        for cat in categories:
            for story in cat.get('stories', []):
                existing = story.get('image_url')
                if existing and isinstance(existing, str) and existing.startswith('/images/cache/'):
                    continue  # Already cached
                sources = story.get('sources', [])
                source_urls = [s['url'] for s in sources if s.get('url', '').startswith('http')]
                if existing and isinstance(existing, str) and existing.startswith('http'):
                    tasks.append((story, 'direct', existing))
                elif source_urls:
                    tasks.append((story, 'source', source_urls))

        if not tasks:
            continue

        print(f'  {jname}: {len(tasks)} stories need images...')

        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {}
            for story, task_type, payload in tasks:
                if task_type == 'direct':
                    futures[pool.submit(validate_and_cache, payload)] = story
                else:
                    futures[pool.submit(resolve_image_for_sources, payload)] = story
            for fut in as_completed(futures):
                story = futures[fut]
                try:
                    result = fut.result()
                    if result:
                        story['image_url'] = result
                        modified = True
                        stats['cached'] += 1
                    else:
                        # Omit image_url entirely if we can't validate
                        if 'image_url' in story:
                            del story['image_url']
                        stats['failed'] += 1
                except Exception:
                    stats['failed'] += 1

        if modified:
            jpath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            print(f'  ✅ {jname}: updated')

    return stats


def main():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print('🖼️  CEO Briefing Image Cache')
    print('=' * 40)

    print('\n📄 Processing HTML files...')
    html_stats = process_html_files()

    print('\n📰 Processing category-news JSON...')
    json_stats = process_category_news()

    total_cached = html_stats['cached'] + json_stats['cached']
    total_failed = html_stats['failed'] + json_stats['failed']

    print(f'\n📊 Results: {total_cached} images cached, {total_failed} failed/unavailable')

    # Count cached files
    cached_files = list(CACHE_DIR.glob('*'))
    total_size = sum(f.stat().st_size for f in cached_files)
    print(f'📁 Cache: {len(cached_files)} files, {total_size / 1024 / 1024:.1f}MB')


if __name__ == '__main__':
    main()
