# -*- coding: utf-8 -*-
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BASE = Path('/Users/xand/.openclaw/workspace/ceo-briefing')
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TODAY_EN = 'Thursday, April 30, 2026'
TODAY_JA = '2026年4月30日（木）'
TITLE_DATE = 'Apr 30, 2026'


def gnews(query: str):
    url = 'https://news.google.com/rss/search?q=' + urllib.parse.quote(query) + '&hl=en-US&gl=US&ceid=US:en'
    try:
        xml_text = requests.get(url, headers=HEADERS, timeout=20).text
        root = ET.fromstring(xml_text)
        item = root.find('./channel/item')
        if item is None:
            return {'url': '', 'source': 'Source', 'title': query, 'image': ''}
        link = item.findtext('link') or ''
        source = item.find('source').text if item.find('source') is not None else 'Source'
        title = item.findtext('title') or query
        return {'url': link, 'source': source, 'title': title, 'image': og_image(link)}
    except Exception:
        return {'url': '', 'source': 'Source', 'title': query, 'image': ''}


def og_image(url: str):
    if not url:
        return ''
    try:
        r = requests.get(url, headers=HEADERS, timeout=3)
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', r.text, re.I)
        return html.escape(m.group(1), quote=True) if m else ''
    except Exception:
        return ''


def source_links(items):
    links = []
    for item in items:
        if item.get('url'):
            links.append(f'            <a class="source-link" href="{item["url"]}" target="_blank" rel="noopener">{html.escape(item["source"])} <span class="src-arrow">↗</span></a>')
    return '\n'.join(links)


def fmt_pct(v):
    return ('+' if v >= 0 else '') + f'{v:.2f}%'


def yahoo_series(symbol: str):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1y&interval=1d&includePrePost=false'
    j = requests.get(url, headers=HEADERS, timeout=20).json()['chart']['result'][0]
    closes = [c for c in j['indicators']['quote'][0]['close'] if c is not None]
    return closes


def market_row(name: str, symbol: str, digits=2, suffix=''):
    vals = yahoo_series(symbol)
    last = vals[-1]
    prev = vals[-2]
    week = vals[-6] if len(vals) >= 6 else vals[0]
    month = vals[-22] if len(vals) >= 22 else vals[0]
    ytd = vals[0]
    return (
        name,
        f'{last:,.{digits}f}{suffix}',
        fmt_pct((last / prev - 1) * 100),
        fmt_pct((last / week - 1) * 100),
        fmt_pct((last / month - 1) * 100),
        fmt_pct((last / ytd - 1) * 100),
    )


def story_card(tag, headline, body, sources, ja=False, featured=True):
    tap = 'タップして展開' if ja else 'Tap to expand'
    featured_cls = ' featured' if featured else ''
    japan_cls = ' japan' if ('🇯🇵' in tag or '日本' in tag) else ''
    return f'''        <article class="card{featured_cls} fade-in collapsible" data-image="{sources[0].get('image','') if sources else ''}">
          <span class="card-tag{japan_cls}">{tag}</span>
          <h3 class="card-headline">{headline}</h3>
          <div class="tap-hint">{tap}</div>
          <p class="card-body">{body}</p>
          <div class="card-sources">\n{source_links(sources)}\n          </div>
        </article>'''


def table_card(tag, headline, headers, rows, body, sources):
    th = ''.join(f'<th>{h}</th>' for h in headers)
    trs = []
    for row in rows:
        tds = [f'<td class="idx-name">{row[0]}</td>', f'<td class="idx-level">{row[1]}</td>']
        for v in row[2:]:
            klass = 'chg-pos' if str(v).startswith('+') else 'chg-neg' if str(v).startswith('-') else ''
            tds.append(f'<td class="{klass}">{v}</td>')
        trs.append('<tr>' + ''.join(tds) + '</tr>')
    return f'''        <article class="card fade-in" data-image="{sources[0].get('image','') if sources else ''}">
          <span class="card-tag">{tag}</span>
          <h3 class="card-headline">{headline}</h3>
          <table class="index-table"><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>
          <p class="card-body" style="margin-top: 1rem;">{body}</p>
          <div class="card-sources">\n{source_links(sources)}\n          </div>
        </article>'''


src = {
    'yen_shorts': gnews('Investors reload yen shorts in intervention test Reuters'),
    'boj_split': gnews('Bank of Japan keeps rates steady but hawkish split points to June hike Reuters'),
    'core_infl': gnews("Japan's core inflation stays below BOJ target, energy risks grow Reuters"),
    'takaichi_budget': gnews('Japan PM Takaichi rules out extra budget for now Reuters'),
    'japan_exports': gnews('Japan exports rise for seventh month as AI demand blunts Mideast risks for now Reuters'),
    'japan_bullrun': gnews("Japan's record bull run under threat as Mideast war clouds earnings season Reuters"),
    'real_wages': gnews('Japan real wages grow for first time in 13 months boosting BOJ hike case Reuters'),
    'nojima': gnews("Japan's Nojima to buy Hitachi's consumer appliances unit for more than $630 million Reuters"),
    'us_stocks': gnews('Oil soars US stocks end muted on Iran worries with earnings Fed in focus Reuters'),
    'trading_day': gnews('Trading Day Fed dissent oil ascent Reuters'),
    'pg_hit': gnews('P&G warns of $1 billion profit hit in fiscal 2027 from higher oil prices Reuters'),
    'automakers': gnews('Foreign automakers threaten to pull cheapest models from US without trade deal Reuters'),
    'europe_shares': gnews('European shares hit three-week low as earnings data and Iran conflict weigh Reuters'),
    'ecb_energy': gnews("Energy crisis raises concerns for financial stability ECB's Panetta warns Reuters"),
    'china_fuel': gnews('China curtailing not banning fuel exports shipping data shows Reuters'),
    'sk_hynix': gnews('SK Hynix to invest about $13 bln in a new South Korea plant to meet AI memory demand Reuters'),
    'india_rupee': gnews("Rupee's slide to record low puts Indian central bank back on the defensive Reuters"),
    'worldbank_energy': gnews('World Bank forecasts 24% surge in energy prices in 2026 due to Middle East war Reuters'),
    'trump_choices': gnews('One month into Iran war only hard choices for Trump Reuters'),
    'airlines': gnews('Airlines cancel flights amid Middle East conflict Reuters'),
    'lula': gnews("Brazil's Lula assails Trump threats says leaders should seek respect Reuters"),
    'mercosur_canada': gnews('Canadian trade team headed to Brasilia next week for Mercosur talks Reuters'),
    'chile_us': gnews('Chile US to sign mining and security agreements Reuters'),
    'vanuatu': gnews('Australia Vanuatu security agreement delayed Reuters'),
    'iranian_players': gnews("Five Iranian women's soccer players granted humanitarian visas in Australia Reuters"),
    'yahoo': {'url': 'https://finance.yahoo.com/', 'source': 'Yahoo Finance', 'title': 'Yahoo Finance', 'image': ''},
}

EQ_ROWS = [
    market_row('Nikkei 225', '^N225'),
    market_row('S&P 500', '^GSPC'),
    market_row('Dow Jones', '^DJI'),
    market_row('Nasdaq', '^IXIC'),
    market_row('Euro Stoxx 50', '^STOXX50E'),
    market_row('Shanghai Comp', '000001.SS'),
    market_row('Sensex', '^BSESN'),
    market_row('Bovespa', '^BVSP', 0),
    market_row('ASX 200', '^AXJO'),
]
FX_ROWS = [
    market_row('USD/JPY', 'JPY=X', 3),
    market_row('EUR/USD', 'EURUSD=X', 4),
    market_row('DXY', 'DX-Y.NYB', 3),
    market_row('US 10Y Treasury', '^TNX', 3, '%'),
]
CMD_ROWS = [
    market_row('Gold', 'GC=F'),
    market_row('Silver', 'SI=F', 3),
    market_row('WTI Crude', 'CL=F'),
    market_row('Bitcoin', 'BTC-USD'),
    market_row('Ethereum', 'ETH-USD'),
]
market_sources = [src['us_stocks'], src['worldbank_energy'], src['china_fuel'], src['yahoo']]

nikkei_level, nikkei_day = EQ_ROWS[0][1], EQ_ROWS[0][2]
usdjpy_level, usdjpy_day = FX_ROWS[0][1], FX_ROWS[0][2]
wti_level, wti_day = CMD_ROWS[2][1], CMD_ROWS[2][2]

japan = [
    {
        'tag': '🇯🇵 JAPAN · MARKET CLOSE',
        'headline': f'Tokyo finished the afternoon with Nikkei at {nikkei_level} ({nikkei_day}) because AI-linked exporters still had earnings support, even as oil risk and yen stress capped the upside.',
        'body': '<strong>Why it happened:</strong> the close reflected two forces pulling in opposite directions. Exporters and semiconductor-linked names kept attracting buyers because AI demand and overseas revenue translation still look supportive. But the rally stayed constrained because a weaker yen and higher crude simultaneously raise Japan’s import bill. The causal chain was exporter earnings support offset by imported-cost anxiety.',
        'sources': [src['japan_bullrun'], src['japan_exports']],
    },
    {
        'tag': '🇯🇵 JAPAN · FX / INTERVENTION',
        'headline': f'The yen stayed at the center of the afternoon because USD/JPY hovered near {usdjpy_level} ({usdjpy_day}), drawing fresh tests of whether Tokyo will move beyond verbal intervention.',
        'body': '<strong>Why it happened:</strong> traders rebuilt short-yen positions because global capital still prefers the dollar when oil, war risk, and rate uncertainty all rise together. That creates a self-reinforcing loop: dollar demand weakens the yen, a weaker yen worsens Japan’s imported inflation problem, and that in turn raises pressure on officials to sound tougher.',
        'sources': [src['yen_shorts']],
    },
    {
        'tag': '🇯🇵 JAPAN · BOJ / POLICY',
        'headline': 'The BOJ looked more conflicted than calm because its hawkish internal split says inflation risk is real, but the external shock is making the timing of the next hike much harder.',
        'body': '<strong>Why it happened:</strong> the bank cannot ignore yen weakness and imported energy inflation forever, so a hawkish split matters. But it also cannot tighten carelessly into a shock that is being driven by oil and geopolitics rather than broad-based domestic overheating. The cause of the mixed signal is that Japan now has inflation pressure without a clean growth backdrop.',
        'sources': [src['boj_split'], src['core_infl']],
    },
    {
        'tag': '🇯🇵 JAPAN · INFLATION / HOUSEHOLDS',
        'headline': 'Soft core inflation and better real wages told the same story in the afternoon: Japan has some domestic resilience, but not enough yet to make imported inflation feel safe.',
        'body': '<strong>Why it happened:</strong> real wages matter because they are the bridge from higher prices to sustainable spending power. But core inflation staying below target means the BOJ still lacks proof that demand-led inflation has fully taken over. The reason this matters is causal: if inflation is still mostly imported, policy makers have less room to welcome it.',
        'sources': [src['real_wages'], src['core_infl']],
    },
    {
        'tag': '🇯🇵 JAPAN · FISCAL POLICY',
        'headline': 'Prime Minister Takaichi kept extra-budget firepower in reserve because Tokyo still sees this as a shock to monitor before spending aggressively into it.',
        'body': '<strong>Why it happened:</strong> holding back now preserves fiscal ammunition for a scenario where oil stays high long enough to damage demand and sentiment more deeply. If the government spent immediately, it could waste room on the first wave and have less flexibility later. The cause is sequencing: wait for evidence that a price shock is becoming a broader economic shock.',
        'sources': [src['takaichi_budget']],
    },
    {
        'tag': '🇯🇵 JAPAN · CORPORATE',
        'headline': 'Nojima’s move on Hitachi’s appliance unit stood out because Japanese corporates are trying to lock in controllable advantages while geopolitics makes the macro backdrop less controllable.',
        'body': '<strong>Why it happened:</strong> when boards cannot control oil, war risk, or currencies, they focus on scale, procurement, and distribution. The acquisition fits that logic. It is a defensive growth move, driven by the idea that operational leverage is worth more when the external environment is unstable.',
        'sources': [src['nojima']],
    },
]

global_regions = {
    'North America': [
        ('North America', 'Wall Street lost momentum because higher oil stopped looking like a headline spike and started looking like an earnings and Fed problem.', '<strong>Why it happened:</strong> once traders believe crude will stay elevated, they have to reprice three things at once: inflation, margins, and policy flexibility. That is why oil strength weighed on stocks even before every company had updated guidance.', [src['us_stocks'], src['trading_day']]),
        ('North America', 'P&G’s profit warning mattered because it showed the energy shock is already moving from macro talk into corporate math.', '<strong>Why it happened:</strong> oil raises transport, packaging, and petrochemical-input costs at the same time. The warning was not about one bad quarter, it was about a cost chain that becomes hard to offset if crude stays high.', [src['pg_hit']]),
        ('North America', 'Foreign automakers threatened to pull cheaper models from the US because tariff uncertainty is starting to distort product decisions, not just trade rhetoric.', '<strong>Why it happened:</strong> if tariffs remain sticky, low-margin models become less viable in the US market. That forces automakers to defend profitability by cutting offerings, which is why trade policy is now affecting consumer choice directly.', [src['automakers']]),
    ],
    'Europe': [
        ('Europe', 'European shares slid to a three-week low because weak earnings, softer data, and the Iran-linked oil shock all hit at the same time.', '<strong>Why it happened:</strong> Europe had no clean offset. Earnings disappointed, data did not reassure, and higher oil threatened both inflation and demand. The selloff came from that stacked causal chain rather than any single data point.', [src['europe_shares']]),
        ('Europe', 'The ECB kept warning about financial-stability risk because an energy shock can tighten credit even before policy rates move.', '<strong>Why it happened:</strong> higher energy costs squeeze households and companies first, then show up as weaker borrowers and more fragile markets. That is why the ECB is worried about transmission into the financial system, not only CPI prints.', [src['ecb_energy']]),
        ('Europe', 'The region’s tariff nerves stayed elevated because Europe now has to manage weaker growth and external trade pressure at the same time.', '<strong>Why it happened:</strong> when domestic momentum is already fading, trade conflict becomes more damaging because companies have less pricing power and governments have less fiscal room. Europe’s anxiety is caused by that double bind.', [src['europe_shares'], src['ecb_energy']]),
    ],
    'Asia ex-Japan': [
        ('Asia ex-Japan', 'China’s curbs on fuel exports kept regional energy markets tight because even a partial reduction from such a large supplier forces neighbors to bid harder for supply.', '<strong>Why it happened:</strong> Beijing is prioritizing domestic stability, and that means fewer barrels available to ease the regional squeeze. The effect is causal and mechanical: less export availability means higher competition and firmer prices elsewhere in Asia.', [src['china_fuel']]),
        ('Asia ex-Japan', 'SK Hynix remained one of the few clean risk-on stories because AI memory demand still looks strong enough to overcome the broader geopolitical gloom.', '<strong>Why it happened:</strong> investors are treating high-bandwidth memory as a real spending cycle, not a hope trade. That is why the stock can outperform even when the wider region is coping with oil and rates stress.', [src['sk_hynix']]),
        ('Asia ex-Japan', 'India’s rupee stayed under pressure because oil is worsening both the import bill and the central bank’s room to ease.', '<strong>Why it happened:</strong> higher crude hurts India twice, first through the current account and second through inflation. That dual hit is why the RBI is being pushed back onto the defensive.', [src['india_rupee']]),
    ],
    'Middle East & Africa': [
        ('Middle East & Africa', f'WTI crude at {wti_level} ({wti_day}) remained the region’s most global export because the war is still being priced as a supply and transport risk, not just a military event.', '<strong>Why it happened:</strong> markets are baking in the possibility of prolonged shipping disruption, higher insurance costs, and spillover into refined fuels. Oil stays elevated because traders are pricing duration, not just danger.', [src['worldbank_energy'], src['airlines']]),
        ('Middle East & Africa', 'The World Bank’s energy-price warning hit harder in the afternoon because it quantified what a prolonged conflict could do to inflation and growth.', '<strong>Why it happened:</strong> once institutions start attaching numbers to the shock, markets move from vague fear to measurable downgrade risk. That makes the scenario feel more durable and therefore more damaging.', [src['worldbank_energy']]),
        ('Middle East & Africa', 'Airlines kept cancelling flights because airspace, fuel costs, and insurance assumptions have all become unstable at once.', '<strong>Why it happened:</strong> carriers are responding to a cluster of risks, not one isolated threat. When routing certainty disappears, normal scheduling economics stop working, which is why cancellations persist.', [src['airlines'], src['trump_choices']]),
    ],
    'Latin America': [
        ('Latin America', 'Lula’s latest criticism of Trump mattered because Brazil wants to protect both domestic political legitimacy and bargaining leverage in a harsher global trade climate.', '<strong>Why it happened:</strong> public pushback helps Lula avoid looking subordinate abroad or weak at home. The cause is not just ideology, it is also coalition management and strategic signaling.', [src['lula']]),
        ('Latin America', 'Mercosur and Canada talks gained significance because both sides want alternative trade channels before tariff politics gets even less predictable.', '<strong>Why it happened:</strong> diversification is more valuable when access to major markets becomes politically unstable. The talks are accelerating because both parties are hedging future trade risk.', [src['mercosur_canada']]),
        ('Latin America', 'Chile’s mining and security agreements with the US reflected how critical minerals have become part of geopolitics, not just commodity trade.', '<strong>Why it happened:</strong> Washington wants supply security while Chile wants capital and strategic relevance. Those incentives line up because minerals now sit inside national-security planning.', [src['chile_us']]),
    ],
    'Oceania': [
        ('Oceania', 'The Australia-Vanuatu security delay mattered because Pacific alignment is proving slower and more negotiated than Canberra would prefer.', '<strong>Why it happened:</strong> island governments want support without appearing fully locked into one camp too quickly. The delay comes from that balancing act between strategic urgency and local political consent.', [src['vanuatu']]),
        ('Oceania', 'Australia’s humanitarian visas for Iranian women footballers stood out because war displacement and women’s rights have become politically inseparable in this conflict.', '<strong>Why it happened:</strong> Canberra could frame the decision as both humanitarian action and values signaling. It moved because the case carried symbolic weight far beyond routine migration processing.', [src['iranian_players']]),
        ('Oceania', 'Regional politics stayed tied to Middle East spillovers because energy costs and alliance choices are now shaping even seemingly local Pacific decisions.', '<strong>Why it happened:</strong> when global shocks lift fuel costs and sharpen security competition, smaller regional negotiations take on larger strategic meaning. The cause is interconnection, not coincidence.', [src['vanuatu'], src['worldbank_energy']]),
    ],
}

japan_ja = [
    ('🇯🇵 日本・大引け', f'日経平均は{nikkei_level}（{nikkei_day}）で午後を終えた。AI関連の輸出株に業績期待が残る一方、油高と円安が上値を抑えたからだ。', '<strong>なぜそうなったか：</strong>買い手はAI需要と外貨建て収益の追い風を評価したが、同じ円安が輸入コストとエネルギー負担も押し上げるため、全面高にはなりにくかった。つまり午後の東京は、輸出企業の強さと輸入インフレ不安の綱引きで決まった。', [src['japan_bullrun'], src['japan_exports']]),
    ('🇯🇵 日本・為替/介入', f'USD/JPYが{usdjpy_level}（{usdjpy_day}）近辺で推移し、東京が口先介入で足りるのかを改めて試す午後になった。', '<strong>なぜ円が重いか：</strong>油高、戦争リスク、金利不透明感が重なる局面では、資金はなおドルへ向かいやすい。そのドル需要が円安を進め、円安が輸入インフレを悪化させ、当局の警戒発言を強めるという連鎖になっている。', [src['yen_shorts']]),
    ('🇯🇵 日本・日銀', '日銀は落ち着いているというより、かなり難しい位置にいる。タカ派の分裂はインフレ圧力を示すが、外部ショックの中で利上げ時期はむしろ難しくなっているからだ。', '<strong>なぜ難しいか：</strong>円安とエネルギー高を放置もしづらい一方で、原油主導のショックに対し内需が十分強いとも言えない。つまり日本はいま、インフレ圧力はあるのに成長の確信が弱いという、最も政策判断が難しい組み合わせにいる。', [src['boj_split'], src['core_infl']]),
    ('🇯🇵 日本・物価/家計', 'コア物価の弱さと実質賃金の改善は、午後の日本経済を同時に説明した。内需の耐久力は少しあるが、輸入インフレを安心して受け止められるほどではない。', '<strong>なぜ重要か：</strong>実質賃金は、物価上昇が家計の購買力に耐えられるかを測る橋になる。しかしコア物価がなお弱いということは、需要主導の持続インフレにはまだ距離がある。だから政策当局は「歓迎できる物価上昇」と言い切れない。', [src['real_wages'], src['core_infl']]),
    ('🇯🇵 日本・財政政策', '高市首相が補正予算を温存したのは、今のショックをまず見極め、長引く場合に備えて弾を残したいからだ。', '<strong>なぜ今は温存か：</strong>ここで早く使い切ると、油高が需要悪化まで波及した局面で対応余地が狭まる。今回の判断は消極姿勢というより、「価格ショックが景気ショックに変わるか」を待つ順番の問題。', [src['takaichi_budget']]),
    ('🇯🇵 日本・企業', 'ノジマによる日立家電事業の買収が目立ったのは、地政学でマクロが読みにくいほど、企業が自分で握れる強みを先に押さえようとしているからだ。', '<strong>なぜこの案件か：</strong>原油も為替も戦争も企業には制御できない。だからこそ、規模、調達、流通といった運営面の優位は相対的に価値が上がる。今回の買収はその防御的成長の発想に沿っている。', [src['nojima']]),
]

global_regions_ja = {
    '北米': [
        ('北米', '米株は勢いを失った。原油高が一時的な見出しではなく、企業収益とFRBの両方に効く問題として再評価されたからだ。', '<strong>なぜ株に重いか：</strong>原油高が長引くと、インフレ、利益率、政策自由度を同時に悪化させる。市場はその「期間」を織り込み直し始めた。', [src['us_stocks'], src['trading_day']]),
        ('北米', 'P&Gの警告が重いのは、エネルギーショックがマクロの話から企業の算式に移ったことを示すからだ。', '<strong>なぜ象徴的か：</strong>物流、包装、石化原料が同時に上がると、価格転嫁だけでは吸収しにくい。つまり油高はもう抽象論ではなく、利益計画を直接傷つけ始めている。', [src['pg_hit']]),
        ('北米', '自動車各社が安価モデル縮小を示唆したのは、関税不透明感が通商論争ではなく商品構成そのものを変え始めたからだ。', '<strong>なぜ消費者に効くか：</strong>低採算車ほど関税コストを吸収しにくいため、メーカーは利益防衛のためにラインアップを見直す。通商政策が購買選択を直接変える段階に入っている。', [src['automakers']]),
    ],
    '欧州': [
        ('欧州', '欧州株が3週間ぶり安値をつけたのは、決算の弱さ、景気データの鈍化、イラン発の油高が同時に効いたからだ。', '<strong>なぜ下げが重いか：</strong>欧州には明確な相殺材料が少なかった。収益、景気、エネルギーの三方向から圧力がかかり、単発の悪材料ではなく複合要因の下げになった。', [src['europe_shares']]),
        ('欧州', 'ECBが金融安定リスクを強調するのは、エネルギー高が政策金利より先に信用環境を締める可能性があるからだ。', '<strong>なぜCPIだけではないか：</strong>光熱費上昇は家計と企業の余力を削り、その後で借り手の弱体化や市場の脆さとして表れる。ECBはその伝播経路を警戒している。', [src['ecb_energy']]),
        ('欧州', '欧州の通商不安が残るのは、内需が弱い局面ほど外部の摩擦がより深い打撃になるからだ。', '<strong>なぜ今こそ痛いか：</strong>成長が弱い時は、企業の価格転嫁力も政府の財政余力も乏しい。だから通商圧力は普段以上に重くなる。', [src['europe_shares'], src['ecb_energy']]),
    ],
    'アジア（日本除く）': [
        ('アジア（日本除く）', '中国の燃料輸出抑制は、全面禁止でなくても地域の需給を十分締める。中国ほどの供給国が少し絞るだけで周辺国の調達競争が強まるからだ。', '<strong>なぜ効くか：</strong>中国は国内安定を優先しており、その分だけ外向け供給が減る。結果としてアジア全体で代替調達コストが上がり、価格が固くなる。', [src['china_fuel']]),
        ('アジア（日本除く）', 'SKハイニックスが強いのは、AI向けメモリ需要が地政学不安を打ち消せる数少ない実需として見られているからだ。', '<strong>なぜ逆行高か：</strong>高帯域メモリは期待ではなく支出計画で支えられている。だからリスクオフ地合いでも選ばれやすい。', [src['sk_hynix']]),
        ('アジア（日本除く）', 'インドのルピーが弱いのは、原油高が輸入代金と利下げ余地の両方を悪化させるからだ。', '<strong>なぜRBIが苦しいか：</strong>油高は経常赤字を悪化させるだけでなく、インフレ警戒も強める。その二重苦で中銀は守りに回らざるを得ない。', [src['india_rupee']]),
    ],
    '中東・アフリカ': [
        ('中東・アフリカ', f'WTIは{wti_level}（{wti_day}）で、戦争が単なる軍事イベントではなく供給・物流リスクとして値付けされ続けていることを示した。', '<strong>なぜ高止まりか：</strong>市場は供給断絶だけでなく、海運迂回、保険料上昇、精製品への波及まで織り込んでいる。恐怖ではなく期間の価格付けだ。', [src['worldbank_energy'], src['airlines']]),
        ('中東・アフリカ', '世界銀行の警告が重いのは、衝撃の大きさを数字で示し、成長と物価の下振れリスクを定量化したからだ。', '<strong>なぜ午後に効いたか：</strong>機関が数値を出すと、市場は漠然とした不安ではなく具体的な下方修正を考え始める。そこでショックは一段現実味を増す。', [src['worldbank_energy']]),
        ('中東・アフリカ', '航空会社の欠航が続くのは、空域、燃料費、保険、運航確実性が同時に不安定化しているからだ。', '<strong>なぜ長引くか：</strong>単発の安全懸念ではなく、複数コストと複数リスクの重なりだから。通常の運航経済が成立しにくい。', [src['airlines'], src['trump_choices']]),
    ],
    'ラテンアメリカ': [
        ('ラテンアメリカ', 'ルラ大統領の対トランプ批判は、国内政治の正統性と対外交渉力を同時に守る必要があるからだ。', '<strong>なぜ公然とか：</strong>強く言わなければ国内では弱く見え、対外的にも交渉余地を失う。理念だけでなく政権運営の計算がある。', [src['lula']]),
        ('ラテンアメリカ', 'メルコスールとカナダの接近は、主要市場の予見性が落ちる前に代替販路を増やしたいからだ。', '<strong>なぜ今急ぐか：</strong>関税政治が強まるほど、分散先を持つ価値は上がる。交渉加速の原因はリスク分散。', [src['mercosur_canada']]),
        ('ラテンアメリカ', 'チリと米国の鉱業・安全保障協定は、重要鉱物が地政学の中核資産になったことを示した。', '<strong>なぜ一体化するか：</strong>米国は供給安定を、チリは資本と戦略的重要性を求める。両者の利害が一致している。', [src['chile_us']]),
    ],
    'オセアニア': [
        ('オセアニア', '豪州とバヌアツの安保協定の遅れは、太平洋での陣取りが豪州の望むほど一直線では進まないことを示した。', '<strong>なぜ遅れるか：</strong>島しょ国は支援を求めつつも、急いで一方の陣営に固定されるようには見られたくない。その政治調整が原因。', [src['vanuatu']]),
        ('オセアニア', '豪州がイラン人女子サッカー選手に人道ビザを出したのは、戦争避難と女性の権利が切り離せない争点になっているからだ。', '<strong>なぜ象徴的か：</strong>通常の移民判断ではなく、人道と価値観のシグナルとして処理された案件だから目立つ。', [src['iranian_players']]),
        ('オセアニア', 'オセアニアの地域政治も中東ショックと無関係ではない。燃料コストと同盟選択が、ローカルな交渉の意味まで変えているからだ。', '<strong>なぜつながるか：</strong>世界的なコスト上昇と安全保障競争が強まるほど、小さな地域協議も大きな戦略文脈に組み込まれる。', [src['vanuatu'], src['worldbank_energy']]),
    ],
}


def build_body(lang='en'):
    if lang == 'en':
        japan_cards = '\n'.join(story_card(x['tag'], x['headline'], x['body'], x['sources']) for x in japan)
        global_cards = []
        for _, items in global_regions.items():
            for tag, headline, body, sources in items:
                global_cards.append(story_card(tag, headline, body, sources))
        global_cards = '\n'.join(global_cards)
        markets = '\n'.join([
            table_card('EQUITIES', 'End-of-day equity snapshot', ['Index', 'Level', 'Daily', 'Weekly', 'Monthly', 'YTD'], EQ_ROWS, '<strong>Why the bigger moves happened:</strong> markets were split by who still had a visible earnings buffer and who mainly inherited the oil shock. Japan and AI-linked tech held up better where demand visibility remained. Regions facing direct energy-import pressure, weaker data, or policy constraints struggled because higher crude looked more durable by the afternoon.', market_sources),
            table_card('FX & RATES', 'Currency and rate pressure points', ['Instrument', 'Level', 'Daily', 'Weekly', 'Monthly', 'YTD'], FX_ROWS, '<strong>Why it matters:</strong> USD/JPY is still the fastest way to read Japan’s policy stress because yen weakness helps exporters while worsening imported inflation. DXY and Treasuries matter because prolonged oil strength makes central banks sound less comfortable. Any move above 2% should be read through the duration of the energy shock, not as isolated noise.', market_sources),
            table_card('COMMODITIES & CRYPTO', 'Commodity and digital-asset close', ['Asset', 'Price', 'Daily', 'Weekly', 'Monthly', 'YTD'], CMD_ROWS, '<strong>Big mover logic:</strong> if crude moves more than 2%, the most likely cause is still conflict duration plus tighter regional fuel supply after China curtailed exports. If silver or crypto swing more than 2%, the better explanation is usually dollar repricing and changing inflation-hedge demand.', market_sources),
            '''        <article class="card fade-in" data-image="'''+(market_sources[0].get('image',''))+'''"><span class="card-tag">HEALTH SCORE</span><h3 class="card-headline">56/100, still fragile, but Tokyo looked somewhat more resilient than the rest of the tape by the close.</h3><p class="card-body"><strong>Why 56:</strong> the afternoon did not become safer, but it did become more differentiated. Japan still had supports from exporters, AI demand, and slightly better household income data, while much of the rest of the world kept absorbing oil, tariff, and growth stress more directly. The score stays below neutral because yen pressure and imported inflation remain unresolved.</p><div class="card-sources">\n'''+source_links(market_sources)+'''\n          </div></article>'''
        ])
        predictions = '''        <article class="card fade-in collapsible" data-image=""><span class="card-tag">TOMORROW</span><h3 class="card-headline">Watch whether Tokyo escalates from verbal yen defense to a clearer intervention or coordination signal if dollar pressure persists.</h3><div class="tap-hint">Tap to expand</div><p class="card-body"><strong>Why it matters:</strong> if the yen weakens further while the BOJ still hesitates, the burden shifts toward the government and the Ministry of Finance. That would turn FX policy into tomorrow’s most important Japan risk, not just a background market story.</p></article>
        <article class="card fade-in collapsible" data-image=""><span class="card-tag">WEEK AHEAD</span><h3 class="card-headline">The next macro test is whether higher energy prices keep spreading from headlines into earnings downgrades, flight disruption, and broader policy tightening.</h3><div class="tap-hint">Tap to expand</div><p class="card-body"><strong>Why it matters:</strong> once consumer companies, airlines, importers, and central banks are all adjusting to the same shock, markets stop pricing fear and start pricing duration. That is when volatility tends to rise more structurally.</p></article>'''
        bottom_line = 'The new afternoon takeaway was not that risk faded, but that <strong>Japan still has more visible buffers than many peers even as the yen-oil squeeze intensifies.</strong> Exporters, AI demand, and modest wage relief kept Tokyo steadier than much of the world. Elsewhere, higher energy prices kept spreading into Wall Street caution, European weakness, India stress, and harder growth math. <strong>Bottom line:</strong> the shock is broadening, but Japan still looks relatively better positioned than most markets to absorb the first round.'
        sub = f'🇯🇵 Tokyo’s late-session tone held because exporters and AI-linked demand cushioned the yen-and-oil squeeze, even as USD/JPY stayed near {usdjpy_level} and the BOJ remained conflicted · Takaichi kept fiscal firepower in reserve while Nojima-style corporate moves showed boards chasing controllable advantages · Globally, higher oil kept spilling into US equities, Europe, India, airlines, and World Bank growth worries · Health Score: 56/100'
        footer = 'CEO Afternoon Briefing · Generated by Sanbot · Thursday, April 30, 2026'
        return f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html" class="active">EN</a><span class="sep">/</span><a href="ja.html">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">59</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_EN} — Afternoon Edition</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">Japan</a><a href="#global" class="nav-pill">Global</a><a href="#markets" class="nav-pill">Markets</a><a href="#predictions" class="nav-pill">Predictions</a><a href="#bottomline" class="nav-pill">Bottom Line</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">Japan Update — In Depth</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">Global — By Continent</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">Markets & Economy</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">Predictions</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''

    japan_cards = '\n'.join(story_card(t, h, b, s, ja=True) for t, h, b, s in japan_ja)
    global_cards = []
    for _, items in global_regions_ja.items():
        for tag, headline, body, sources in items:
            global_cards.append(story_card(tag, headline, body, sources, ja=True))
    global_cards = '\n'.join(global_cards)
    markets = '\n'.join([
        table_card('株式', '引け後マーケット一覧', ['指数', '水準', '日次', '週次', '月次', '年初来'], EQ_ROWS, '<strong>大きな値動きの因果：</strong>今日は「業績の支えが見える市場」と「油高ショックを直接受ける市場」で差がついた。日本やAI関連は相対的に踏ん張った一方、エネルギー輸入圧力や景気減速に近い市場は弱かった。2%超の動きはまずショックの持続期間で読むべき。', market_sources),
        table_card('為替・金利', '通貨と金利の要点', ['指標', '水準', '日次', '週次', '月次', '年初来'], FX_ROWS, '<strong>なぜ重要か：</strong>USD/JPYは日本の政策ストレスを最も早く映す。円安は輸出株の追い風だが、輸入インフレの悪化でもある。DXYと米金利は、油高が長引くほど中銀が楽観を語りにくくなることを示す。2%超の動きは単発ではなくショックの長期化で読む。', market_sources),
        table_card('商品・暗号資産', '商品とデジタル資産の引け', ['資産', '価格', '日次', '週次', '月次', '年初来'], CMD_ROWS, '<strong>大きく動く理由：</strong>原油の2%超変動は、依然として戦争の長期化懸念と中国の輸出抑制による域内燃料逼迫が主因。銀や暗号資産の大きな動きは、今日はドル再評価とインフレヘッジ需要の変化で読むのが自然。', market_sources),
        '''        <article class="card fade-in" data-image="'''+(market_sources[0].get('image',''))+'''"><span class="card-tag">ヘルススコア</span><h3 class="card-headline">56/100、まだ脆いが、引け時点では東京のほうが世界全体よりやや底堅かった。</h3><p class="card-body"><strong>なぜ56か：</strong>安全になったわけではないが、午後は日本に輸出、AI需要、家計所得の改善という支えが残った。一方で世界は油高、通商不安、成長下方圧力をより直接に吸収していた。円安と輸入インフレが未解決なので中立以下だが、相対比較では東京が少し強い。</p><div class="card-sources">\n'''+source_links(market_sources)+'''\n          </div></article>'''
    ])
    predictions = '''        <article class="card fade-in collapsible" data-image=""><span class="card-tag">明日</span><h3 class="card-headline">ドル高が続けば、日本が口先介入から一段強いシグナルへ進むかを注視。</h3><div class="tap-hint">タップして展開</div><p class="card-body"><strong>なぜ重要か：</strong>日銀が簡単に動けないほど、政府・財務省側の為替対応が焦点になる。為替政策が明日の日本市場の主戦場になり得る。</p></article>
    <article class="card fade-in collapsible" data-image=""><span class="card-tag">今週</span><h3 class="card-headline">エネルギー高が見出しで終わるのか、業績下方修正、欠航、政策引き締めへ広がるのかが最大の分岐点。</h3><div class="tap-hint">タップして展開</div><p class="card-body"><strong>なぜそこか：</strong>消費企業、航空、輸入国、中銀が同じショックに反応し始めると、市場は恐怖ではなく期間を値付けする。その段階ではボラティリティが構造的に上がりやすい。</p></article>'''
    bottom_line = '午後に見えた新しい事実は、<strong>リスクが弱まったのではなく、日本にはまだ相対的な緩衝材が残っている</strong>ということだ。輸出、AI需要、賃金改善が東京を支えた一方、世界では油高が米株、欧州、インド、航空、成長見通しへ広く波及した。<strong>結論：</strong>ショックの拡大は続いているが、日本は現時点で第一波への耐久力が比較的高い。'
    sub = f'🇯🇵 東京は、輸出株とAI需要が円安・油高の重しを一部相殺し、USD/JPYは{usdjpy_level}近辺で政策緊張を維持 · 高市首相は財政余力を温存し、企業は買収で握れる優位を取りにいった · 世界では原油高が米株、欧州、インド、航空、世銀の成長警戒へ広がった · Health Score: 56/100'
    footer = 'CEO Afternoon Briefing · Generated by Sanbot · 2026年4月30日（木）'
    return f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html">EN</a><span class="sep">/</span><a href="ja.html" class="active">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">59</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_JA} 午後版</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">日本</a><a href="#global" class="nav-pill">世界</a><a href="#markets" class="nav-pill">市場</a><a href="#predictions" class="nav-pill">予測</a><a href="#bottomline" class="nav-pill">結論</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">日本アップデート</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">世界の動き</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">市場と経済</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">予測</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''


def build_page(path: Path, lang='en'):
    src_html = path.read_text()
    head = src_html.split('<body>')[0] + '<body>\n'
    body = build_body(lang)
    page = re.sub(r'<title>CEO Briefing — [^<]+</title>', f'<title>CEO Briefing — {TITLE_DATE}</title>', head) + body
    path.write_text(page)


build_page(BASE / 'index.html', 'en')
build_page(BASE / 'ja.html', 'ja')
print('updated')
