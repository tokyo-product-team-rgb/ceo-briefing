# -*- coding: utf-8 -*-
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BASE = Path('/Users/xand/.openclaw/workspace/ceo-briefing')
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TODAY_EN = 'Saturday, May 16, 2026'
TODAY_JA = '2026年5月16日（土）'
TITLE_DATE = 'May 16, 2026'
HEALTH = 55


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
    image = next((x.get('image', '') for x in sources if x.get('image')), '')
    return f'''        <article class="card{featured_cls} fade-in collapsible" data-image="{image}">
<span class="card-tag{japan_cls}">{tag}</span>
<h3 class="card-headline">{headline}</h3>
<div class="tap-hint">{tap}</div>
<p class="card-body">{body}</p>
<div class="card-sources">\n{source_links(sources)}\n</div>
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
    image = next((x.get('image', '') for x in sources if x.get('image')), '')
    return f'''        <article class="card fade-in" data-image="{image}">
<span class="card-tag">{tag}</span>
<h3 class="card-headline">{headline}</h3>
<table class="index-table"><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>
<p class="card-body" style="margin-top: 1rem;">{body}</p>
<div class="card-sources">\n{source_links(sources)}\n</div>
</article>'''


src = {
    'yen_defence': gnews('Japan keeps US close as it signals unlimited yen defence Reuters'),
    'boj_hold': gnews("VIEW Investors react to BOJ's decision to hold rates Reuters"),
    'boj_june': gnews('BOJ expected to raise rates to 1.0% in June hike again in October December Reuters'),
    'oecd_japan': gnews('OECD sees Japan raising interest rates to 2% by end-2027 Reuters'),
    'g7_bonds': gnews('Japan finance minister says G7 likely to discuss bond volatility next week Reuters'),
    'japan_firms': gnews('More Japanese firms say no to rate hikes as Iran war clouds outlook Reuters poll Reuters'),
    'toyota_texas': gnews('Toyota files to build $2 billion assembly line in Texas Reuters'),
    'softbank_openai': gnews("SoftBank's OpenAI-related debt in focus as another strong quarter expected Reuters"),
    'us_mfg': gnews('US manufacturing sector holds steady in April input costs hit 4-year high Reuters'),
    'us_russia_waiver': gnews('US renews Russian oil waiver after pressure from countries dealing with Iran war price shocks Reuters'),
    'mexico_tariffs': gnews('US trade rep tells Mexican companies Trump tariffs here to stay Reuters'),
    'bmw': gnews('BMW keeps 2026 guidance shrugs off tariff threat as profit beats expectations Reuters'),
    'eu_deadline': gnews('Trump sets July 4 deadline for EU to comply with trade deal or face much higher tariffs Reuters'),
    'india_credit': gnews('Indian shares climb on Iran peace deal hopes government credit guarantee Reuters'),
    'china_tariffs': gnews("What are China's current tariffs on US energy and agriculture goods Reuters"),
    'oil_supply': gnews('Oil supply shock to worsen as inventories fall further even if conflict ends Reuters'),
    'eu_fuel': gnews('EU to push for jet fuel diversification as Iran war threatens supply Reuters'),
    'sa_rate': gnews('South Africa Kganyago says central bank must keep rate options open amid inflation threat Reuters'),
    'mexico_spain': gnews('Mexico mends ties with Spain in first presidential visit in eight years Reuters'),
    'lula_trump': gnews("Brazil's Lula assails Trump threats says leaders should seek respect Reuters"),
    'argentina_wb': gnews('World Bank plans up to $2 billion guarantee to help Argentina refinance debt Reuters'),
    'australia_flood': gnews('Flash flooding hits Australia Victoria state cars washed out to sea Reuters'),
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
    market_row('US 2Y Treasury', '^IRX', 3, '%'),
]
CMD_ROWS = [
    market_row('WTI Crude', 'CL=F'),
    market_row('Brent Crude', 'BZ=F'),
    market_row('Gold', 'GC=F'),
    market_row('Silver', 'SI=F', 3),
    market_row('Bitcoin', 'BTC-USD'),
    market_row('Ethereum', 'ETH-USD'),
]

nikkei_level, nikkei_day = EQ_ROWS[0][1], EQ_ROWS[0][2]
spx_level, spx_day = EQ_ROWS[1][1], EQ_ROWS[1][2]
usdjpy_level, usdjpy_day = FX_ROWS[0][1], FX_ROWS[0][2]
dxy_level, dxy_day = FX_ROWS[2][1], FX_ROWS[2][2]
us10_level, us10_day = FX_ROWS[3][1], FX_ROWS[3][2]
wti_level, wti_day = CMD_ROWS[0][1], CMD_ROWS[0][2]
brent_level, brent_day = CMD_ROWS[1][1], CMD_ROWS[1][2]
gold_level, gold_day = CMD_ROWS[2][1], CMD_ROWS[2][2]

japan = [
    {
        'tag': '🇯🇵 JAPAN · FX DEFENCE',
        'headline': f'Japan kept the US unusually close on FX messaging this afternoon because officials want markets to believe they can lean harder against disorderly yen selling, even with USD/JPY still at {usdjpy_level} ({usdjpy_day}).',
        'body': '<strong>Why it happened:</strong> Tokyo knows intervention threats only work if Washington is seen as tolerant. The causal chain is diplomatic cover first, stronger anti-speculation signaling second, which is why wording from both sides mattered more than a routine jawbone.',
        'sources': [src['yen_defence'], src['g7_bonds']],
    },
    {
        'tag': '🇯🇵 JAPAN · BOJ HOLD',
        'headline': 'The market treated the BOJ hold as more hawkish than passive because investors heard a pause paired with a shorter fuse on the next hike, not a return to wait-and-see policy.',
        'body': '<strong>Why it happened:</strong> once yen weakness and imported inflation are feeding each other, holding rates steady can still be read as a staging step before action. That is why the reaction centered on timing, not on relief.',
        'sources': [src['boj_hold'], src['yen_defence']],
    },
    {
        'tag': '🇯🇵 JAPAN · RATE PATH',
        'headline': 'The Reuters poll pointing to a June hike to 1.0% and another move later this year mattered because the market now sees policy normalization as a response to real inflation pressure, not just central-bank theater.',
        'body': '<strong>Why it happened:</strong> higher import costs, a weak yen, and sticky global energy prices are raising the credibility cost of waiting. That causal chain is why expectations shifted toward back-to-back normalization instead of one symbolic move.',
        'sources': [src['boj_june'], src['oecd_japan']],
    },
    {
        'tag': '🇯🇵 JAPAN · LONGER-TERM RATES',
        'headline': 'OECD calling for Japan to reach 2% policy rates by end-2027 landed as a bigger deal than the headline suggests because it validates the idea that Japan is exiting emergency money for structural reasons, not for one-off currency optics.',
        'body': '<strong>Why it happened:</strong> outside institutions are reacting to the same chain, more durable inflation, firmer wage transmission, and a weaker tolerance for yen-led price shocks. That gives investors permission to price a steeper path.',
        'sources': [src['oecd_japan'], src['boj_june']],
    },
    {
        'tag': '🇯🇵 JAPAN · POLICY RISK',
        'headline': 'Japan’s finance minister flagging G7 discussion of bond volatility mattered because Tokyo is preparing investors for a world where higher yields are no longer a US problem that Japan can simply import and absorb.',
        'body': '<strong>Why it happened:</strong> if global bond volatility stays high while Japan normalizes, domestic funding costs and fiscal sensitivity both rise. The minister is trying to frame that risk before the market tests the system harder.',
        'sources': [src['g7_bonds'], src['boj_hold']],
    },
    {
        'tag': '🇯🇵 JAPAN · CORPORATE SENTIMENT',
        'headline': 'A Reuters poll showing more Japanese firms oppose further rate hikes is an important afternoon change because the Iran-war cost shock is colliding with domestic normalization just as companies face thinner margin room.',
        'body': '<strong>Why it happened:</strong> higher fuel, shipping, and imported-input costs are already squeezing business plans. Firms are resisting rate hikes not because inflation vanished, but because another tightening step now compounds a geopolitical cost shock.',
        'sources': [src['japan_firms'], src['oil_supply']],
    },
]

global_regions = {
    'North America': [
        ('North America', 'US manufacturing holding steady while input costs hit a four-year high mattered because it showed the economy is not cooling fast enough to give the Fed easy cover, even as inflation pressure is re-accelerating through supply costs.', '<strong>Why it happened:</strong> tariffs, transport stress, and energy costs all pushed inputs higher while demand stayed firm enough to keep factories operating. That combination is exactly why bond yields stay sticky.', [src['us_mfg'], src['us_russia_waiver']]),
        ('North America', 'Washington renewing a Russian-oil waiver after pressure from countries hit by the Iran war mattered because the White House is trying to cap price damage without admitting the broader sanctions architecture is tightening energy markets too much.', '<strong>Why it happened:</strong> once allies start absorbing fuel shocks, the US has to choose between purity and price stability. It chose temporary relief because inflation politics are now more dangerous than policy inconsistency.', [src['us_russia_waiver'], src['oil_supply']]),
        ('North America', 'The US trade message to Mexican companies that Trump tariffs are here to stay mattered because it tells boards to plan for a durable cost regime, not a negotiating bluff.', '<strong>Why it happened:</strong> when firms believe tariffs are sticky, they change sourcing, capex, and hiring. That is why the communication itself moved the story from politics into operations.', [src['mexico_tariffs']]),
    ],
    'Europe': [
        ('Europe', 'BMW holding 2026 guidance despite tariff risk helped sentiment only at the margin because investors saw resilience in one company, not a resolution of Europe’s broader trade and demand problem.', '<strong>Why it happened:</strong> strong current execution can offset some policy fear, but it cannot remove tariff risk. The stock-supportive read came from earnings durability, not from macro improvement.', [src['bmw'], src['eu_deadline']]),
        ('Europe', 'Trump’s July 4 deadline for the EU raised the temperature because it shortens the window for compromise and forces European exporters to price in disruption before supply chains can adapt.', '<strong>Why it happened:</strong> shorter deadlines increase the probability of precautionary behavior, delayed orders, inventory changes, and delayed investment. That uncertainty is the actual economic transmission channel.', [src['eu_deadline'], src['bmw']]),
        ('Europe', 'Brussels pushing jet-fuel diversification showed Europe is treating the Middle East shock as a supply-security problem, not just an oil-price headline.', '<strong>Why it happened:</strong> policymakers are reacting to the chain from Hormuz risk to aviation fuel vulnerability to summer travel costs. Diversification becomes urgent when rerouting and insurance no longer look temporary.', [src['eu_fuel'], src['oil_supply']]),
    ],
    'Asia ex-Japan': [
        ('Asia ex-Japan', 'Indian shares rose on peace-deal hopes and a new credit guarantee because investors concluded New Delhi is trying to cushion the fuel shock before it spills into jobs and SME cash flow.', '<strong>Why it happened:</strong> policy support plus lower immediate war-risk expectations reduced the odds of a sharper domestic slowdown. That is why the market rewarded both the headline and the guarantee.', [src['india_credit']]),
        ('Asia ex-Japan', 'China’s tariff posture on US energy and agriculture mattered because it showed Beijing still wants leverage over politically sensitive sectors while keeping room to calibrate the economic pain.', '<strong>Why it happened:</strong> energy and farm goods are ideal pressure points because they hit US producers and signal resolve without immediately shutting China out of more strategic supply lines.', [src['china_tariffs']]),
        ('Asia ex-Japan', 'Across the region, the afternoon mood stayed fragile because oil-shock risk did not disappear, it was merely offset for a few hours by policy support and peace hopes.', '<strong>Why it happened:</strong> the underlying chain, imported fuel risk to inflation to tighter financial conditions, remains intact. That is why relief rallies have looked tactical rather than durable.', [src['india_credit'], src['oil_supply']]),
    ],
    'Middle East & Africa': [
        ('Middle East & Africa', f'Oil remained the central macro story, with WTI at {wti_level} ({wti_day}) and Brent at {brent_level} ({brent_day}), because traders now expect inventory drawdowns and rerouting costs to outlast any single ceasefire headline.', '<strong>Why it happened:</strong> once inventories fall and shipping patterns change, prices stay elevated even if fighting cools. Markets are pricing duration of disruption, not just today’s battlefield news.', [src['oil_supply']]),
        ('Middle East & Africa', 'Europe’s scramble to diversify jet fuel underlined how far the conflict has spread economically because aviation is now pricing the shock as a logistics problem as much as a crude problem.', '<strong>Why it happened:</strong> airlines and fuel planners are reacting to the chain from maritime risk to fuel availability to higher summer travel costs. That is why procurement strategy is changing now.', [src['eu_fuel'], src['oil_supply']]),
        ('Middle East & Africa', 'South Africa’s central bank keeping its options open mattered because the energy shock is strong enough to delay easing even in economies far from the Gulf.', '<strong>Why it happened:</strong> imported fuel inflation pushes directly into headline CPI and weakens the case for rate cuts. That is why the conflict is traveling through monetary policy, not just commodities.', [src['sa_rate'], src['oil_supply']]),
    ],
    'Latin America': [
        ('Latin America', 'Mexico mending ties with Spain mattered because the government wants more diplomatic and investment flexibility just as North American trade politics get harder.', '<strong>Why it happened:</strong> when US tariff risk rises, Mexico has an incentive to widen its external options. Diplomatic repair is part of an economic hedging strategy.', [src['mexico_spain'], src['mexico_tariffs']]),
        ('Latin America', 'Lula publicly pushing back on Trump threats mattered because Brazil is trying to defend strategic autonomy while warning domestic audiences it will not simply absorb great-power pressure.', '<strong>Why it happened:</strong> stronger rhetoric helps Lula balance nationalism at home with bargaining leverage abroad. The message is political positioning with trade implications attached.', [src['lula_trump']]),
        ('Latin America', 'The World Bank exploring up to $2 billion in guarantees for Argentina mattered because refinancing help is becoming necessary precisely when global funding conditions are getting less forgiving.', '<strong>Why it happened:</strong> higher yields and geopolitical stress make market access harder for fragile borrowers. Multilateral credit support is the bridge being considered to prevent that stress from turning into a funding event.', [src['argentina_wb']]),
    ],
    'Oceania': [
        ('Oceania', 'Flash flooding in Victoria mattered because climate shocks are again becoming an immediate supply and insurance story for Australia, not just a weather story.', '<strong>Why it happened:</strong> when cars are washed out and transport is interrupted, damage flows quickly into logistics, claims costs, and local business disruption. That is why the market relevance is economic, not merely visual.', [src['australia_flood']]),
    ],
}

global_regions_ja = {
    '北米': [
        ('北米', '米製造業が底堅い一方で投入コストが4年ぶり高水準となったのは、景気が十分に冷えず、しかもインフレ圧力が供給側から再加速していることを示した。', '<strong>なぜそうなったか：</strong>関税、輸送混乱、エネルギー高が原材料コストを押し上げた一方、需要は工場稼働を維持できる程度に強かった。この組み合わせが米金利を高止まりさせる。', [src['us_mfg'], src['us_russia_waiver']]),
        ('北米', '米国がロシア産原油の適用除外を延長したのは、イラン戦争由来の価格上昇を和らげる必要が強まったからだ。', '<strong>なぜ方針を緩めたか：</strong>同盟国まで燃料ショックを吸収し始めると、政策の一貫性より物価安定のほうが政治的に重くなる。だから一時的な価格緩和を優先した。', [src['us_russia_waiver'], src['oil_supply']]),
        ('北米', '米通商当局がメキシコ企業に「トランプ関税は残る」と伝えたのは重要だ。企業に一時的な交渉材料ではなく、恒常的なコスト体制として備えさせるメッセージだからだ。', '<strong>なぜ効くか：</strong>関税が長引くと信じた瞬間に、企業は調達、設備投資、採用を変え始める。政治がオペレーションに変わる地点だ。', [src['mexico_tariffs']]),
    ],
    '欧州': [
        ('欧州', 'BMWが関税リスクの中でも2026年見通しを維持したことは安心材料だったが、欧州全体の問題が解決したわけではない。', '<strong>なぜ限定的な好材料か：</strong>個社の実行力は評価できても、関税リスクそのものは残る。市場が見たのはマクロ改善ではなく企業の耐久力だ。', [src['bmw'], src['eu_deadline']]),
        ('欧州', 'トランプ氏のEU向け7月4日期限は緊張を高めた。企業が供給網を調整し切る前に、政策悪化を織り込まざるを得なくなるからだ。', '<strong>なぜ期限が重いか：</strong>短い交渉期限は発注先送り、在庫再編、投資遅延を生む。不確実性そのものが景気を冷やす。', [src['eu_deadline'], src['bmw']]),
        ('欧州', 'EUがジェット燃料の調達多様化を急ぐのは、中東ショックを単なる原油価格問題ではなく、供給安全保障問題として見始めたからだ。', '<strong>なぜ今か：</strong>ホルムズ海峡リスクが航空燃料の調達と夏季旅行コストに直結し始めた。だから調達戦略そのものを動かしている。', [src['eu_fuel'], src['oil_supply']]),
    ],
    'アジア（日本除く）': [
        ('アジア（日本除く）', 'インド株が和平期待と信用保証策で上がったのは、政府が燃料ショックを雇用や中小企業資金繰りへ波及する前に食い止めようとしていると見られたからだ。', '<strong>なぜ反応したか：</strong>政策支援と戦争リスクの一時緩和が、急減速の確率を下げたと受け止められた。だから市場は両方を同時に買った。', [src['india_credit']]),
        ('アジア（日本除く）', '中国の対米エネルギー・農産物関税姿勢も重要だった。北京が政治的に効く分野で圧力を維持しつつ、より戦略的な供給網では柔軟性を残そうとしているからだ。', '<strong>なぜこの分野か：</strong>エネルギーと農業は米国内で痛みが見えやすく、中国側には交渉カードとして使いやすい。', [src['china_tariffs']]),
        ('アジア（日本除く）', '地域全体では午後も地合いが脆いままだった。原油ショックが消えたのではなく、政策支援と和平期待で一時的に相殺されただけだからだ。', '<strong>なぜ持続的ではないか：</strong>輸入燃料高からインフレ、金融引き締まりへつながる根本の連鎖は残ったままだからだ。', [src['india_credit'], src['oil_supply']]),
    ],
    '中東・アフリカ': [
        ('中東・アフリカ', f'原油は依然としてマクロの中心で、WTIは{wti_level}（{wti_day}）、Brentは{brent_level}（{brent_day}）だった。市場が在庫減少と迂回コストの長期化を織り込んでいるからだ。', '<strong>なぜ高止まりするか：</strong>停戦見出しが出ても、在庫が減り海運が変われば価格はすぐには戻らない。市場は「混乱の長さ」を買っている。', [src['oil_supply']]),
        ('中東・アフリカ', 'EUがジェット燃料多様化を急ぐのは、紛争が原油価格ニュースから実体経済の物流問題へ広がっている証拠だ。', '<strong>なぜ波及したか：</strong>海上リスクが燃料供給、航空コスト、夏の旅行価格へ連鎖しているためだ。', [src['eu_fuel'], src['oil_supply']]),
        ('中東・アフリカ', '南ア中銀が選択肢を開いたままにしたのも重要だ。湾岸から遠い国でも、エネルギー起点のインフレで利下げを急げなくなっているからだ。', '<strong>なぜ世界の金融政策問題か：</strong>輸入燃料高はCPIを押し上げ、緩和余地を削る。紛争が商品市況から金融政策へ伝播している。', [src['sa_rate'], src['oil_supply']]),
    ],
    'ラテンアメリカ': [
        ('ラテンアメリカ', 'メキシコがスペインとの関係修復を進めたのは、北米の通商政治が厳しくなる中で外交と投資の選択肢を増やしたいからだ。', '<strong>なぜ今か：</strong>米関税リスクが上がるほど、メキシコは外部オプションを広げる必要がある。外交修復は経済ヘッジでもある。', [src['mexico_spain'], src['mexico_tariffs']]),
        ('ラテンアメリカ', 'ルラ大統領がトランプ氏の脅しに反発したのは、対外圧力をそのまま受け入れない姿勢を国内外に示すためだ。', '<strong>なぜ強く言うか：</strong>国内では主権の演出になり、対外的には交渉力の維持につながる。政治メッセージだが通商含意を持つ。', [src['lula_trump']]),
        ('ラテンアメリカ', '世界銀行がアルゼンチン向けに最大20億ドル保証を検討しているのは、世界の資金調達環境が悪化する中で借り換え支援が必要になっているからだ。', '<strong>なぜ今必要か：</strong>金利上昇と地政学ストレスで脆弱国の市場アクセスが難しくなる。多国間保証は資金イベント化を防ぐ橋になる。', [src['argentina_wb']]),
    ],
    'オセアニア': [
        ('オセアニア', 'ビクトリア州の鉄砲水は、豪州で気候ショックが再び即時の物流・保険問題になっていることを示した。', '<strong>なぜ経済ニュースか：</strong>車両被害や輸送寸断は、そのまま保険金、物流遅延、地域ビジネスの停止につながるからだ。', [src['australia_flood']]),
    ],
}

pred_en = [
    ('TOMORROW', 'Tomorrow’s first question is whether Tokyo turns today’s coordinated yen-defence language into a harder policy signal, because verbal support without follow-through tends to fade quickly.', '<strong>Why to watch it:</strong> if officials escalate from messaging to action, exporters, JGBs, and bank stocks could all reprice together.'),
    ('WEEK AHEAD', 'The broader risk for next week is that oil, yields, and tariffs stop being separate headlines and start acting like one tightening machine.', '<strong>Why to watch it:</strong> once energy shock, funding costs, and trade friction reinforce each other, earnings revisions usually arrive with a lag, then all at once.'),
]

pred_ja = [
    ('明日', '明日の焦点は、東京が今日の円防衛メッセージをさらに強い政策シグナルへ変えるかどうかだ。言葉だけでは効果が長続きしにくいからだ。', '<strong>なぜ見るべきか：</strong>発言が実行へ進めば、輸出株、国債、銀行株が同時に再評価されやすい。'),
    ('来週', '来週の大きなリスクは、原油高、金利高、関税が別々の見出しではなく、一つの引き締め装置として効き始めることだ。', '<strong>なぜ重要か：</strong>エネルギー、資金コスト、通商摩擦が重なると、業績下方修正は遅れて一気に来やすい。'),
]


def render_page(lang='en'):
    is_ja = lang == 'ja'
    title = 'CEO Afternoon Briefing'
    edition_date = f'{TODAY_JA} 午後版' if is_ja else f'{TODAY_EN} — Afternoon Edition'
    edition_sub = (
        f'🇯🇵 The afternoon change was that Japan moved from passive yen anxiety to active policy defense, while the rest of the world kept absorbing oil, tariff, and yield stress at the same time · Health Score: {HEALTH}/100'
        if not is_ja else
        f'🇯🇵 午後の本当の変化は、日本が受け身の円不安から能動的な政策防衛へ移ったことだ。一方で世界は原油高、関税、金利高を同時に吸収し続けた · Health Score: {HEALTH}/100'
    )
    nav = [('japan', '日本' if is_ja else 'Japan'), ('global', '世界' if is_ja else 'Global'), ('markets', '市場' if is_ja else 'Markets'), ('predictions', '予測' if is_ja else 'Predictions'), ('bottomline', '結論' if is_ja else 'Bottom Line')]
    jp_cards = japan if not is_ja else [
        {'tag': '🇯🇵 日本・円防衛', 'headline': f'日本が為替で米国との歩調を unusually close に見せたのは、USD/JPYが{usdjpy_level}（{usdjpy_day}）でも無秩序な円売りにはより強く対抗できると市場に信じさせたいからだ。', 'body': '<strong>なぜそうなったか：</strong>介入示唆はワシントンの容認が見えているほど効く。外交的な後ろ盾が先にあり、その上で投機筋への牽制が強まる。だから今回は言い回し自体に重みがあった。', 'sources': [src['yen_defence'], src['g7_bonds']]},
        {'tag': '🇯🇵 日本・日銀据え置き', 'headline': '今回の日銀据え置きが「安心材料」ではなく「よりタカ派の待機」と受け止められたのは、次の利上げまでの猶予が短いと市場が見たからだ。', 'body': '<strong>なぜそう読むか：</strong>円安と輸入インフレが相互に強め合う局面では、据え置きでも次の行動準備と見なされる。市場の反応が安堵よりタイミングに向かったのはそのためだ。', 'sources': [src['boj_hold'], src['yen_defence']]},
        {'tag': '🇯🇵 日本・利上げパス', 'headline': 'ロイター調査で6月に1.0%、年後半に追加利上げとの見方が強まったのは、正常化が演出ではなく実際の物価圧力への対応だと見られているからだ。', 'body': '<strong>なぜそうなったか：</strong>輸入コスト高、円安、エネルギー高止まりで、待つことの信認コストが上がっている。その連鎖が、一回限りではなく連続的な正常化観測につながった。', 'sources': [src['boj_june'], src['oecd_japan']]},
        {'tag': '🇯🇵 日本・中長期金利', 'headline': 'OECDが2027年末までに政策金利2%を見込んだのは、日本が一時的な為替対応ではなく構造的に超緩和を出るとの見方を補強した。', 'body': '<strong>なぜ重要か：</strong>外部機関も、インフレの持続性、賃金波及、円安ショック耐性の低下という同じ因果を見ている。だから市場はより急な金利パスを価格に乗せやすくなる。', 'sources': [src['oecd_japan'], src['boj_june']]},
        {'tag': '🇯🇵 日本・政策リスク', 'headline': '財務相がG7で債券ボラティリティ議論の可能性に触れたのは、金利上昇がもはや米国だけの問題ではなく、日本の調達環境にも直結すると見ているからだ。', 'body': '<strong>なぜ今言うか：</strong>世界の債券変動が高いまま日本が正常化すると、資金調達コストと財政の感応度が同時に上がる。そのリスクを先回りで市場に意識させている。', 'sources': [src['g7_bonds'], src['boj_hold']]},
        {'tag': '🇯🇵 日本・企業心理', 'headline': 'ロイター調査で利上げに否定的な企業が増えたのは、イラン戦争起点のコストショックと国内正常化が同時進行し、利益余地が薄くなっているからだ。', 'body': '<strong>なぜ企業が嫌がるか：</strong>燃料、海運、輸入原材料がすでに重く、そこへ金利上昇が重なると計画が崩れやすい。つまりインフレがないから反対なのではなく、ショックが重なり過ぎているからだ。', 'sources': [src['japan_firms'], src['oil_supply']]},
    ]
    region_source = global_regions if not is_ja else global_regions_ja
    pred_source = pred_en if not is_ja else pred_ja

    jp_html = '\n'.join(story_card(x['tag'], x['headline'], x['body'], x['sources'], ja=is_ja) for x in jp_cards)
    global_html = []
    for region, items in region_source.items():
        for tag, headline, body, sources in items:
            global_html.append(story_card(tag, headline, body, sources, ja=is_ja))
    global_html = '\n'.join(global_html)
    markets = '\n'.join([
        table_card('EQUITIES' if not is_ja else '株式', 'End-of-day equity snapshot' if not is_ja else '主要株価指数', ['Index' if not is_ja else '指数', 'Level' if not is_ja else '水準', 'Daily' if not is_ja else '日次', 'Weekly' if not is_ja else '週次', 'Monthly' if not is_ja else '月次', 'YTD'], EQ_ROWS, '<strong>Why the bigger moves happened:</strong> anything beyond a routine move was still being driven by the same three-way squeeze, oil, yields, and tariff risk. Japan underperformed because policy tightening risk landed on top of it.' if not is_ja else '<strong>大きな動きの理由：</strong>通常以上の変動は、原油高、金利高、関税リスクの三重圧力で説明できる。日本が弱かったのは、その上に政策正常化リスクまで乗ったからだ。', [src['boj_hold'], src['us_mfg'], src['yahoo']]),
        table_card('FX & RATES' if not is_ja else '為替・金利', 'Currency and rate pressure points' if not is_ja else '為替・金利の要点', ['Instrument' if not is_ja else '項目', 'Level' if not is_ja else '水準', 'Daily' if not is_ja else '日次', 'Weekly' if not is_ja else '週次', 'Monthly' if not is_ja else '月次', 'YTD'], FX_ROWS, f'<strong>{"Why it matters" if not is_ja else "なぜ重要か"}:</strong> USD/JPY at {usdjpy_level} and the US 10-year at {us10_level} were the two cleanest tightening gauges of the afternoon because they transmit policy stress directly into Japanese assets and global funding conditions.' if not is_ja else f'<strong>なぜ重要か：</strong>USD/JPY {usdjpy_level} と米10年債 {us10_level} は、午後の引き締まり度合いを最も端的に示した。日本資産と世界の資金調達環境へ直接効くからだ。', [src['yen_defence'], src['us_mfg'], src['yahoo']]),
        table_card('COMMODITIES & CRYPTO' if not is_ja else '商品・暗号資産', 'Commodity and digital-asset close' if not is_ja else '商品・暗号資産', ['Asset' if not is_ja else '資産', 'Price' if not is_ja else '価格', 'Daily' if not is_ja else '日次', 'Weekly' if not is_ja else '週次', 'Monthly' if not is_ja else '月次', 'YTD'], CMD_ROWS, f'<strong>{"Big mover logic" if not is_ja else "大きな変動の因果"}:</strong> oil stayed bid because supply risk now looks persistent, while gold at {gold_level} ({gold_day}) had to fight a stronger dollar instead of enjoying a clean haven bid.' if not is_ja else f'<strong>大きな変動の因果：</strong>原油が強いのは供給不安が長引くと見られているからで、金はドル高に押され、安全資産として素直に買われにくかった。', [src['oil_supply'], src['eu_fuel'], src['yahoo']]),
        story_card('HEALTH SCORE' if not is_ja else 'HEALTH SCORE', f'{HEALTH}/100, because Japan gained policy clarity but the global system grew tighter as oil, yields, and tariffs all kept pressing in the same direction.' if not is_ja else f'{HEALTH}/100, 日本は政策の輪郭が見えた一方で、世界全体は原油高、金利高、関税圧力が同じ方向に効き続け、引き締まりが強まったからだ。', '<strong>Why 55:</strong> clearer Japanese signaling helped reduce one uncertainty, but it did not offset the larger tightening impulse coming from energy, funding costs, and trade friction.' if not is_ja else '<strong>なぜ55か：</strong>日本のシグナル明確化で不確実性は一つ減ったが、エネルギー、資金コスト、通商摩擦から来る大きな引き締め圧力は相殺できなかった。', [src['yen_defence'], src['oil_supply'], src['us_mfg']], ja=is_ja, featured=False)
    ])
    pred_html = '\n'.join(story_card(tag, head, body, [src['yen_defence'], src['oil_supply']] if i == 0 else [src['us_mfg'], src['eu_deadline'], src['oil_supply']], ja=is_ja) for i, (tag, head, body) in enumerate(pred_source))
    bottom = 'The real afternoon change was that <strong>Japan shifted from simply enduring yen weakness to actively preparing a defense across FX, rates, and messaging, while the rest of the world kept getting tighter through oil, tariffs, and yields.</strong> <strong>Bottom line:</strong> Tokyo looks more willing to act, but the global macro backdrop looks less forgiving.' if not is_ja else '午後の本当の変化は、<strong>日本が円安をただ耐える段階から、為替・金利・メッセージを使った防衛準備へ移ったこと</strong>だ。一方で世界は原油高、関税、金利高でさらに締まった。<strong>結論：</strong>東京は動く意思を強めたが、世界マクロはより厳しくなった。'
    return f'''<!DOCTYPE html>
<html lang="{'ja' if is_ja else 'en'}">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>CEO Briefing — {TITLE_DATE}</title>
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<style>
:root{{--bg:#f9f9f9;--surface:#fff;--text:#111;--muted:#666;--border:#e8e5e1;--accent:#1d736c;--pill:#eceae7;--serif:Georgia,serif;--sans:'Hanken Grotesk',sans-serif}}
*{{box-sizing:border-box}} body{{margin:0;font-family:var(--sans);background:var(--bg);color:var(--text);line-height:1.7}} h1,h2,h3{{font-family:var(--serif);font-weight:500}}
.masthead{{padding:2.5rem 1.25rem 1.25rem;text-align:center;position:relative}} .lang-toggle{{position:absolute;top:.75rem;right:1rem;font-size:.75rem}} .lang-toggle a{{text-decoration:none;color:var(--muted)}} .lang-toggle a.active{{color:var(--text)}}
.edition-sub{{max-width:900px;margin:.75rem auto 0;color:#444}} .divider-bar{{width:60px;height:3px;background:#111;margin:1rem auto 0}} .nav-pills{{display:flex;gap:.6rem;justify-content:center;flex-wrap:wrap;padding:0 1rem 1rem}} .nav-pill{{background:var(--pill);padding:.45rem .9rem;border-radius:999px;text-decoration:none;color:#333;font-size:.85rem;font-weight:600}}
.container{{max-width:920px;margin:0 auto;padding:0 1.25rem 3rem}} .section{{margin:2.2rem 0}} .section-header{{display:flex;align-items:center;gap:.6rem;border-bottom:2px solid #111;padding-bottom:.65rem;margin-bottom:1.1rem}} .cards{{display:flex;flex-direction:column;gap:1rem}}
.card,.bottom-line{{background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:1.05rem 1.1rem}} .card-tag{{font-size:.74rem;font-weight:700;color:var(--accent)}} .card-headline{{font-size:1.14rem;line-height:1.35;margin:.35rem 0 .55rem}} .tap-hint{{font-size:.73rem;color:var(--muted);margin-bottom:.45rem}} .card-body{{display:none;color:#444}} .collapsible{{cursor:pointer}} .collapsible.expanded .card-body{{display:block}}
.card-sources{{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:.7rem}} .source-link{{color:var(--accent);text-decoration:none;font-size:.82rem;font-weight:600}} .index-table{{width:100%;border-collapse:collapse;font-size:.92rem}} .index-table th,.index-table td{{padding:.45rem .4rem;border-bottom:1px solid var(--border);text-align:left}} .idx-level{{font-variant-numeric:tabular-nums}} .chg-pos{{color:#0b7a3b}} .chg-neg{{color:#b42318}} .footer{{max-width:920px;margin:0 auto 2rem;padding:0 1.25rem;text-align:center;color:var(--muted);font-size:.82rem}}
</style>
</head>
<body>
<header class="masthead"><div class="lang-toggle"><a href="index.html" class="{'active' if not is_ja else ''}">EN</a><span class="sep">/</span><a href="ja.html" class="{'active' if is_ja else ''}">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><h1>{title}</h1><div class="edition-date">{edition_date}</div><div class="edition-sub">{edition_sub}</div><div class="divider-bar"></div></div></header>
<nav class="nav-pills">{''.join(f'<a href="#{k}" class="nav-pill">{v}</a>' for k, v in nav)}</nav>
<main class="container">
<section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">{'日本アップデート' if is_ja else 'Japan Update — In Depth'}</h2></div><div class="cards">{jp_html}</div></section>
<section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">{'世界の動き' if is_ja else 'Global — By Continent'}</h2></div><div class="cards">{global_html}</div></section>
<section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">{'市場と経済' if is_ja else 'Markets & Economy'}</h2></div><div class="cards">{markets}</div></section>
<section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">{'予測' if is_ja else 'Predictions'}</h2></div><div class="cards">{pred_html}</div></section>
<section class="section" id="bottomline"><div class="bottom-line"><h3>{'💡 結論' if is_ja else '💡 Bottom Line'}</h3><p>{bottom}</p></div></section>
</main>
<footer class='footer'><p>CEO Afternoon Briefing · Generated by Sanbot · {TODAY_JA if is_ja else TODAY_EN}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters via Google News RSS, Yahoo Finance</p></footer>
<script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script>
<script src='audio-player.js'></script>
</body></html>'''


BASE.joinpath('index.html').write_text(render_page('en'))
BASE.joinpath('ja.html').write_text(render_page('ja'))
print('generated')
