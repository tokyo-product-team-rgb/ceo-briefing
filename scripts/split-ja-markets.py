#!/usr/bin/env python3
"""Post-process ja.html to split the combined markets table into separate stories matching English structure."""
import re, sys

def split_markets(html):
    # Find the combined markets card with the big table
    pattern = r'(<article\s+class="card[^"]*"[^>]*>)\s*<span class="card-tag[^"]*">[^<]*</span>\s*<h3 class="card-headline">グローバル株式・債券・商品・通貨</h3>\s*(<table class="index-table">.*?</table>)\s*(.*?)(</article>)'
    m = re.search(pattern, html, re.DOTALL)
    if not m:
        print("  Combined markets card not found — may already be split")
        return html

    card_tag = m.group(1)
    table_html = m.group(2)
    summary_html = m.group(3).strip()
    
    # Parse the table rows
    header_match = re.search(r'<thead>(.*?)</thead>', table_html, re.DOTALL)
    body_match = re.search(r'<tbody>(.*?)</tbody>', table_html, re.DOTALL)
    if not header_match or not body_match:
        print("  Could not parse table structure")
        return html
    
    rows = re.findall(r'<tr>(.*?)</tr>', body_match.group(1), re.DOTALL)
    
    # Categorize rows by content
    equity_keywords = ['s&p', 'ダウ', 'ナスダック', 'nasdaq', '日経', 'nikkei', 'topix', 'kospi', 'hang', 'ハンセン', 'asx', 'dax', 'sensex', '上海', 'vix', 'stoxx']
    commodity_keywords = ['原油', 'wti', 'brent', 'ブレント', 'ゴールド', 'gold', 'シルバー', 'silver', '天然ガス', 'natural gas', '銅', 'copper']
    currency_keywords = ['ドル円', 'usd/jpy', 'eur/usd', 'ユーロ', 'gbp', 'ポンド', 'aud', '豪ドル', 'dxy', 'ルピー', 'inr', 'cnh', '人民元']
    bond_keywords = ['米10年', '米国債', 'jgb', 'ドイツ', 'bund', '英国', 'gilt', '債', 'treasury']
    crypto_keywords = ['ビットコイン', 'bitcoin', 'btc', 'イーサリアム', 'ethereum', 'eth']
    
    equities, commodities, currencies, bonds, crypto = [], [], [], [], []
    
    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        if not cells:
            continue
        name = cells[0].lower().strip()
        name_clean = re.sub(r'<[^>]+>', '', name)
        
        if any(k in name_clean for k in equity_keywords):
            equities.append(row)
        elif any(k in name_clean for k in crypto_keywords):
            crypto.append(row)
        elif any(k in name_clean for k in commodity_keywords):
            commodities.append(row)
        elif any(k in name_clean for k in currency_keywords):
            currencies.append(row)
        elif any(k in name_clean for k in bond_keywords):
            bonds.append(row)
        else:
            equities.append(row)  # default to equities
    
    print(f"  Split: {len(equities)} equities, {len(commodities)} commodities, {len(currencies)} currencies, {len(bonds)} bonds, {len(crypto)} crypto")
    
    # Build replacement HTML
    def make_story(headline, tag, rows_list, columns, has_signal=False):
        cols = columns
        if has_signal and 'シグナル' not in cols:
            cols = cols + ['シグナル']
        
        header_row = ''.join(f'<th>{c}</th>' for c in cols)
        body_rows = '\n              '.join(f'<tr>{r}</tr>' for r in rows_list)
        
        return f'''<article class="card fade-in">
          <span class="card-tag">{tag}</span>
          <h3 class="card-headline">{headline}</h3>
          <table class="index-table">
            <thead><tr>{header_row}</tr></thead>
            <tbody>
              {body_rows}
            </tbody>
          </table>
        </article>'''
    
    base_cols = ['指数', '水準', '日次', '週次', '月次', '年初来']
    
    stories = []
    if equities:
        stories.append(make_story('世界株式指数', '主要指数', equities, base_cols))
    if commodities:
        stories.append(make_story('主要商品', '商品動向', commodities, ['商品', '価格', '日次', '週次', '月次', '年初来']))
    if currencies:
        stories.append(make_story('主要通貨ペア', '為替動向', currencies, ['通貨ペア', 'レート', '日次', '月次', 'シグナル']))
    if bonds:
        stories.append(make_story('国債利回り', '金利動向', bonds, ['国', '10年利回り', '日次', '月次', 'シグナル']))
    if crypto:
        stories.append(make_story('デジタル資産', '暗号資産', crypto, ['資産', '価格', '日次', '月次', '年初来']))
    
    replacement = '\n\n        '.join(stories)
    
    # Replace the original combined card
    html = html[:m.start()] + replacement + html[m.end():]
    return html

if __name__ == '__main__':
    filepath = '/Users/xand/.openclaw/workspace/ceo-briefing/ja.html'
    with open(filepath) as f:
        html = f.read()
    
    print("Processing ja.html...")
    new_html = split_markets(html)
    
    if new_html != html:
        with open(filepath, 'w') as f:
            f.write(new_html)
        print("  ✅ Split combined markets table into separate stories")
    else:
        print("  No changes needed")
