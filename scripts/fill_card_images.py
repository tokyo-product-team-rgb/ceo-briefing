from __future__ import annotations

import html
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = Path('/Users/xand/.openclaw/workspace/ceo-briefing')
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TIMEOUT = 3


def og_image(url: str) -> str:
    if not url:
        return ''
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', r.text, re.I)
        return html.escape(m.group(1), quote=True) if m else ''
    except Exception:
        return ''


for path in sorted(BASE.glob('*.html')):
    soup = BeautifulSoup(path.read_text(), 'html.parser')
    changed = False
    for card in soup.select('article.card'):
        source = card.select_one('.card-sources a[href]')
        if not card.has_attr('data-image'):
            card['data-image'] = ''
            changed = True
        if card.get('data-image'):
            continue
        if source:
            img = og_image(source['href'])
            if img:
                card['data-image'] = img
                changed = True
    if changed:
        path.write_text(str(soup))
        print(path.name)
