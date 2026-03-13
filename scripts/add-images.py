#!/usr/bin/env python3
"""Post-process briefing HTML files to add og:image URLs from source links."""
import re, sys, os, urllib.request, ssl
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed

# Timeout for fetching og:image
TIMEOUT = 4
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_og_image(url):
    """Fetch a URL and extract og:image meta tag."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; bot)'})
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            # Read only first 50KB to find og:image quickly
            html = resp.read(50000).decode('utf-8', errors='ignore')
            m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
            if not m:
                m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
            if m:
                img = m.group(1)
                if img.startswith('http'):
                    return img
    except Exception:
        pass
    return None

def extract_source_urls(card_html):
    """Extract href URLs from a card's HTML."""
    return re.findall(r'href=["\']([^"\']+)["\']', card_html)

def get_headline(card_html):
    """Extract headline text from card."""
    m = re.search(r'class="card-headline"[^>]*>(.*?)</h3>', card_html, re.DOTALL)
    if m:
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()
    return None

def search_news_image(query):
    """Search for a news article and grab its og:image."""
    try:
        encoded = urllib.request.quote(query[:100])
        # Search Google News for the headline, grab first result's og:image
        search_url = f"https://www.google.com/search?q={encoded}&tbm=nws"
        req = urllib.request.Request(search_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            html = resp.read(100000).decode('utf-8', errors='ignore')
            # Find first news result URL
            urls = re.findall(r'href="/url\?q=(https?://[^&"]+)', html)
            for u in urls[:3]:
                u = urllib.request.unquote(u)
                if 'google.com' in u:
                    continue
                img = get_og_image(u)
                if img:
                    return img
    except Exception:
        pass
    return None

def process_file(filepath):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r') as f:
        html = f.read()
    
    # Find all card elements
    cards = list(re.finditer(r'(<article\s+class="card[^"]*"[^>]*>)(.*?)(</article>)', html, re.DOTALL))
    if not cards:
        print(f"  No cards found in {filepath}")
        return
    
    # Collect source URLs per card
    url_tasks = {}
    search_tasks = {}
    for i, m in enumerate(cards):
        tag, body, _ = m.group(1), m.group(2), m.group(3)
        if 'data-image="http' in tag:
            continue  # Already has an image
        urls = extract_source_urls(body)
        urls = [u for u in urls if u.startswith('http') and 'fonts.google' not in u]
        if urls:
            url_tasks[i] = urls[0]
        else:
            headline = get_headline(body)
            if headline:
                search_tasks[i] = headline
    
    total = len(url_tasks) + len(search_tasks)
    if not total:
        print(f"  No cards need images in {filepath}")
        return
    
    print(f"  Fetching og:image for {len(url_tasks)} cards (direct) + {len(search_tasks)} (search) in {os.path.basename(filepath)}...")
    
    # Fetch og:images in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {}
        for idx, url in url_tasks.items():
            futures[pool.submit(get_og_image, url)] = idx
        for idx, query in search_tasks.items():
            futures[pool.submit(search_news_image, query)] = idx
        for fut in as_completed(futures):
            idx = futures[fut]
            img = fut.result()
            if img:
                results[idx] = img
    
    print(f"  Found {len(results)}/{total} images")
    
    if not results:
        return
    
    # Replace card tags with data-image attributes
    # Work backwards to preserve offsets
    new_html = html
    for i in sorted(results.keys(), reverse=True):
        m = cards[i]
        old_tag = m.group(1)
        img_url = results[i]
        if 'data-image=' in old_tag:
            new_tag = re.sub(r'data-image="[^"]*"', f'data-image="{img_url}"', old_tag)
        else:
            new_tag = old_tag.replace('>', f' data-image="{img_url}">', 1)
        new_html = new_html[:m.start(1)] + new_tag + new_html[m.end(1):]
    
    with open(filepath, 'w') as f:
        f.write(new_html)
    print(f"  ✅ Updated {os.path.basename(filepath)}")

if __name__ == '__main__':
    base = '/Users/xand/.openclaw/workspace/ceo-briefing'
    files = [
        'index.html', 'ja.html',
        'ai-review.html', 'vc-review.html', 'energy-review.html',
        'space-review.html', 'health-wellness-review.html',
        'longevity-review.html', 'sports-entertainment-review.html',
        'ai-review-ja.html', 'vc-review-ja.html', 'energy-review-ja.html',
        'space-review-ja.html', 'health-wellness-review-ja.html',
        'longevity-review-ja.html', 'sports-entertainment-review-ja.html',
    ]
    for f in files:
        path = os.path.join(base, f)
        if os.path.exists(path):
            print(f"Processing {f}...")
            process_file(path)
