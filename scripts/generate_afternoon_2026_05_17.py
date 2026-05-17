# -*- coding: utf-8 -*-
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BASE = Path('/Users/xand/.openclaw/workspace/ceo-briefing')
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TODAY_EN = 'Sunday, May 17, 2026'
TODAY_JA = '2026年5月17日（日）'
TITLE_DATE = 'May 17, 2026'
HEALTH = 58


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
    'asia_ai': gnews('Asia stocks AI enthusiasm Trump Xi summit Reuters'),
    'us_japan_fx': gnews('US Japan agree excess FX volatility undesirable Bessent Reuters'),
    'boj_masu': gnews('BOJ board member Masu calls for early rate hike Reuters'),
    'kuroda': gnews('Ex BOJ chief Kuroda sees yen intervention impact as short-lived Reuters'),
    'japan_tanker': gnews('Japan linked crude oil tanker passes through Strait of Hormuz Reuters'),
    'toyota_iran': gnews('Toyota expects hit from effects of Iran war Reuters'),
    'softbank_ai': gnews('SoftBank explores homegrown AI servers with Nvidia Foxconn Reuters'),
    'anthropic_megabanks': gnews('Japan megabanks gain access to Anthropic Mythos Reuters'),
    'bmw': gnews('BMW keeps 2026 guidance tariff threat profit beats expectations Reuters'),
    'eu_deadline': gnews('Trump sets July 4 deadline for EU trade deal Reuters'),
    'india_credit': gnews('India approves credit guarantee support businesses hit by Middle East crisis Reuters'),
    'airlines': gnews('Airlines tackle fuel cost surge with price hikes outlook cuts Reuters'),
    'hormuz_attack': gnews('Hormuz ship attack Iran shipping risk Reuters'),
    'sa_rate': gnews('South Africa central bank rate options open inflation threat Reuters'),
    'lula': gnews("Brazil Lula satisfied after meeting Trump Reuters"),
    'venezuela': gnews('Venezuela opening move in LatAm geoeconomic reset Reuters'),
    'mexico_steel': gnews('Mexico require federal projects use local steel response US tariffs Reuters'),
    'argentina_risk': gnews('Argentina country risk return to capital markets Reuters'),
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
us10_level, us10_day = FX_ROWS[3][1], FX_ROWS[3][2]
wti_level, wti_day = CMD_ROWS[0][1], CMD_ROWS[0][2]
brent_level, brent_day = CMD_ROWS[1][1], CMD_ROWS[1][2]
gold_level, gold_day = CMD_ROWS[2][1], CMD_ROWS[2][2]

japan_en = [
    ('🇯🇵 JAPAN · MARKET CLOSE', f'Tokyo’s latest close left the Nikkei at {nikkei_level} ({nikkei_day}) because afternoon buyers kept chasing the AI complex, but the rally stayed incomplete as stronger-yen risk capped exporters.', '<strong>Why it happened:</strong> global AI momentum pulled money into chip-linked names, but every broad risk-on attempt ran into the same causal brake, traders feared that firmer US-Japan FX coordination and a more hawkish BOJ tone could squeeze exporters through the currency channel.', [src['asia_ai'], src['us_japan_fx']]),
    ('🇯🇵 JAPAN · FX / DIPLOMACY', f'Bessent saying the US and Japan agree excess FX volatility is undesirable mattered immediately because it gave Tokyo more cover to resist disorderly yen selling with USD/JPY still at {usdjpy_level} ({usdjpy_day}).', '<strong>Why it happened:</strong> intervention talk works better when markets think Washington will tolerate it. The causal chain is diplomatic permission first, stronger Japanese signaling second, which is why a wording change shifted the afternoon narrative.', [src['us_japan_fx'], src['kuroda']]),
    ('🇯🇵 JAPAN · BOJ PATH', 'BOJ board member Masu calling for an early rate hike changed the tone because it suggested yen weakness is no longer just a Ministry of Finance problem, it is entering the BOJ reaction function.', '<strong>Why it happened:</strong> once a weak currency feeds imported inflation and credibility risk, the central bank cannot stay patient forever. Markets heard Masu as a warning that rate normalization could be pulled forward if pass-through worsens.', [src['boj_masu'], src['us_japan_fx']]),
    ('🇯🇵 JAPAN · POLICY LIMITS', 'Kuroda warning that yen intervention effects are short-lived mattered because it pushed investors to ask what follows jawboning, namely tighter rates, bigger intervention, or both.', '<strong>Why it happened:</strong> spot defense can slow speculation, but it rarely reverses a move when US-Japan rate differentials still favor the dollar. That is why Kuroda’s caution raised pressure for a fuller policy package instead of calming markets.', [src['kuroda'], src['boj_masu']]),
    ('🇯🇵 JAPAN · CORPORATE COST SHOCK', 'Toyota flagging a multibillion-dollar earnings hit from the Iran war was the clearest corporate warning of the afternoon because fuel, shipping, and parts costs are now large enough to show up in guidance.', '<strong>Why it happened:</strong> the conflict raises energy bills, lengthens logistics routes, and disrupts supplier timing at once. Toyota matters because it turns a geopolitical shock into an earnings problem for Japan’s flagship manufacturer.', [src['toyota_iran'], src['japan_tanker']]),
    ('🇯🇵 JAPAN · STRATEGIC AI', 'SoftBank exploring homegrown AI servers with Nvidia and Foxconn stood out because Japanese groups are trying to localize strategic compute before geopolitics and tariffs make foreign dependence more expensive.', '<strong>Why it happened:</strong> AI demand is rising just as hardware supply chains are getting politically riskier. Building more of the stack under Japanese influence is both a growth bet and a resilience hedge.', [src['softbank_ai'], src['anthropic_megabanks']]),
]

japan_ja = [
    ('🇯🇵 日本・引け後の評価', f'東京の直近引けで日経平均が{nikkei_level}（{nikkei_day}）となったのは、午後もAI関連に買いが続いた一方、円高警戒が輸出株の上値を抑えたからだ。', '<strong>なぜそうなったか：</strong>世界のAI物色が半導体周辺へ資金を呼び込んだが、米日為替協調や日銀タカ派化への警戒が強まり、輸出主導の全面高にはなり切れなかった。', [src['asia_ai'], src['us_japan_fx']]),
    ('🇯🇵 日本・為替外交', f'ベッセント発言で「過度な為替変動は望ましくない」と米日が歩調を合わせたことは重要だ。USD/JPYが{usdjpy_level}（{usdjpy_day}）でも、日本が無秩序な円売りに対抗しやすくなるからだ。', '<strong>なぜ重要か：</strong>為替介入の示唆は、米国の黙認が見えるほど効く。外交的な容認が先にあり、その上で日本の牽制力が増すので、文言自体が相場の意味を変えた。', [src['us_japan_fx'], src['kuroda']]),
    ('🇯🇵 日本・日銀パス', '増氏が早期利上げを示唆したことで、円安は財務省だけの課題ではなく、日銀の反応関数にも入り始めたと市場が受け止めた。', '<strong>なぜそう読むか：</strong>通貨安が輸入インフレと政策信認に波及すると、日銀は待ち続けにくくなる。市場は、円安の波及が強まれば正常化前倒しもあり得ると見た。', [src['boj_masu'], src['us_japan_fx']]),
    ('🇯🇵 日本・政策の限界', '黒田前総裁が円介入の効果は短命と示唆したことは、次に必要なのが口先介入だけでなく、金利や追加措置の組み合わせだと市場に意識させた。', '<strong>なぜそうなるか：</strong>日米金利差がドル優位のままなら、為替介入だけでは流れを反転させにくい。だから発言は安心材料ではなく、追加対応圧力として読まれた。', [src['kuroda'], src['boj_masu']]),
    ('🇯🇵 日本・企業コスト', 'トヨタがイラン戦争による巨額の利益押し下げを示したのは、燃料、海運、部品コストがついに企業ガイダンスへ直接出始めたからだ。', '<strong>なぜ重いか：</strong>紛争はエネルギー代を上げ、物流を長くし、供給のタイミングも乱す。日本の旗艦企業でそれが表面化したことで、地政学が業績問題に変わった。', [src['toyota_iran'], src['japan_tanker']]),
    ('🇯🇵 日本・戦略AI', 'ソフトバンクがNvidia、Foxconnと国産寄りのAIサーバーを探る動きが目立ったのは、地政学と関税で海外依存コストが上がる前に、計算資源の主導権を確保したいからだ。', '<strong>なぜ今か：</strong>AI需要が伸びる一方で、ハードウェア供給網は政治リスクを増している。日本主導の比率を高めることは、成長投資であると同時に耐久性の確保でもある。', [src['softbank_ai'], src['anthropic_megabanks']]),
]

global_en = {
    'North America': [
        ('North America', f'US equities stayed near highs with the S&P 500 at {spx_level} ({spx_day}) because AI momentum is still stronger than macro fear, and hopes for a Trump-Xi meeting reduced the odds of an immediate tariff escalation.', '<strong>Why it happened:</strong> investors kept buying visible AI capex demand while treating summit diplomacy as a possible brake on the next trade shock. The rally stayed selective because neither story removed inflation or oil risk.', [src['asia_ai']]),
        ('North America', 'Washington’s FX message mattered beyond Japan because it showed the US is willing to stabilize allied markets selectively rather than run a uniformly hard line everywhere.', '<strong>Why it happened:</strong> the White House wants to preserve alliance cohesion while keeping pressure on rivals. That selective flexibility is why the yen story became a policy signal instead of just another currency wobble.', [src['us_japan_fx']]),
        ('North America', 'Airlines moving to fare hikes and outlook cuts was a real-economy warning because fuel inflation has gotten too large to absorb quietly in margins.', '<strong>Why it happened:</strong> higher jet fuel, insurance, and rerouting costs hit at the same time. That triple squeeze forces executives to reprice capacity rather than wait for oil to normalize on its own.', [src['airlines'], src['hormuz_attack']]),
    ],
    'Europe': [
        ('Europe', 'BMW holding 2026 guidance despite tariff risk helped sentiment only modestly because investors saw resilience in one company, not a resolution of Europe’s trade problem.', '<strong>Why it happened:</strong> strong execution can cushion the stock, but it cannot erase the margin threat if tariffs persist. The market rewarded durability, not macro relief.', [src['bmw'], src['eu_deadline']]),
        ('Europe', 'Trump’s July 4 deadline for the EU raised the temperature because it compresses negotiation time and forces companies to plan for disruption before supply chains can adapt.', '<strong>Why it happened:</strong> short deadlines change behavior immediately, firms delay investment, rethink inventories, and protect cash because they fear policy conditions will worsen faster than operations can adjust.', [src['eu_deadline'], src['bmw']]),
        ('Europe', 'Europe remained fragile to the Middle East shock because its weak growth base leaves less room to absorb another imported energy squeeze than the US.', '<strong>Why it happened:</strong> higher oil acts like a tax on households and industry at the same time. That hurts more when domestic demand was already soft before the latest shipping stress arrived.', [src['airlines'], src['hormuz_attack']]),
    ],
    'Asia ex-Japan': [
        ('Asia ex-Japan', 'India’s credit guarantee was one of the clearest policy responses of the day because New Delhi decided it was cheaper to protect working capital now than let fuel-shock stress spread into jobs and SME finance.', '<strong>Why it happened:</strong> imported energy inflation quickly damages transport, cash flow, and confidence. The guarantee is meant to break that causal chain before it becomes a domestic slowdown.', [src['india_credit'], src['airlines']]),
        ('Asia ex-Japan', 'The Hormuz shipping-risk debate mattered for the rest of Asia because import-dependent economies feel the damage through freight, LNG, and crude bills well before they feel it through official GDP data.', '<strong>Why it happened:</strong> the region is structurally exposed to maritime energy routes, so investors trade the story first as a logistics-cost shock and only later as a diplomatic story.', [src['hormuz_attack'], src['india_credit']]),
        ('Asia ex-Japan', 'AI enthusiasm outperformed old-economy cyclicals across the region because investors still see compute and semis as the one growth pocket least dependent on cheap fuel or easy trade politics.', '<strong>Why it happened:</strong> when the macro backdrop worsens, capital crowds into sectors with visible capex demand and strategic support. That is why AI held up while broader risk appetite stayed fragile.', [src['asia_ai']]),
    ],
    'Middle East & Africa': [
        ('Middle East & Africa', f'Crude remained the macro hinge, with WTI at {wti_level} ({wti_day}) and Brent at {brent_level} ({brent_day}), because traders still see shipping disruption as persistent enough to keep inventories and insurance costs elevated.', '<strong>Why it happened:</strong> markets are pricing duration risk, not just one headline. Even without a fresh supply outage, rerouting and precautionary stocking keep the energy shock alive.', [src['hormuz_attack'], src['airlines']]),
        ('Middle East & Africa', 'Airlines cutting outlooks showed the conflict is broadening from an oil headline into an earnings problem across travel and logistics.', '<strong>Why it happened:</strong> longer routes burn more fuel, higher insurance raises operating costs, and uncertainty reduces schedule efficiency. That three-part hit is why guidance moved today.', [src['airlines'], src['hormuz_attack']]),
        ('Middle East & Africa', 'South Africa’s central bank keeping its options open mattered because even economies far from the Gulf are being forced into a more cautious inflation posture as energy risk returns.', '<strong>Why it happened:</strong> imported fuel pressure can delay easing cycles everywhere. South Africa is the reminder that the conflict is traveling through monetary policy, not just commodities.', [src['sa_rate'], src['hormuz_attack']]),
    ],
    'Latin America': [
        ('Latin America', 'Lula sounding satisfied after meeting Trump mattered because Brazil is trying to de-risk its US relationship before tariff politics harden further.', '<strong>Why it happened:</strong> Brazil benefits from keeping access to both Washington and global commodity demand. Diplomatic warmth is a hedge against a harsher external policy environment.', [src['lula']]),
        ('Latin America', 'Venezuela becoming an opening move in a wider LatAm geoeconomic reset mattered because investors are starting to reprice which countries get capital, sanctions relief, and trade access.', '<strong>Why it happened:</strong> once geopolitics changes the regional pecking order, money does not re-rate one country in isolation. Venezuela is being watched as the first signal of a broader reshuffle.', [src['venezuela'], src['lula']]),
        ('Latin America', 'Mexico requiring local steel in federal projects showed how US tariff pressure is cascading through the region because governments are starting to build their own industrial defenses instead of waiting for Washington to soften.', '<strong>Why it happened:</strong> when US trade policy hardens, neighbors try to prevent imported damage from crushing domestic producers. That turns a bilateral tariff dispute into regional supply-chain rewiring.', [src['mexico_steel'], src['argentina_risk']]),
    ],
    'Oceania': [
        ('Oceania', 'Oceania stayed quieter than other regions, but the region is still exposed because higher energy and shipping costs hit importers fast once Asian freight routes get more expensive.', '<strong>Why it happened:</strong> distance magnifies logistics inflation, so even without a fresh local headline, the same Middle East shipping stress keeps pressuring costs through the trade channel.', [src['hormuz_attack'], src['airlines']]),
    ],
}

global_ja = {
    '北米': [
        ('北米', f'米株はS&P 500が{spx_level}（{spx_day}）近辺を維持した。AI物色の強さがマクロ不安をまだ上回り、トランプ・習会談期待が次の関税悪化リスクを少し和らげたからだ。', '<strong>なぜそうなったか：</strong>投資家は見えやすいAI投資需要を買い続け、首脳会談が通商ショックを少し遅らせる可能性も織り込んだ。ただしインフレや油高は残るため、全面高にはなっていない。', [src['asia_ai']]),
        ('北米', '米国の為替メッセージは日本以外にも効いた。ワシントンが全方位で硬直するのではなく、同盟国市場は選別的に安定させる姿勢を見せたからだ。', '<strong>なぜ重要か：</strong>対外強硬姿勢を保ちつつ同盟の結束も守るには、味方市場の混乱を一部抑える必要がある。その柔軟性が円の話を政策シグナルに変えた。', [src['us_japan_fx']]),
        ('北米', '航空会社が値上げと見通し引き下げに動いたのは実体経済の警告だ。燃料インフレがもう静かに利益率で吸収できる水準ではなくなったからだ。', '<strong>なぜ今表面化したか：</strong>ジェット燃料、保険、迂回コストが同時に上がると、一時要因として処理できない。だから経営計画の側が動き始める。', [src['airlines'], src['hormuz_attack']]),
    ],
    '欧州': [
        ('欧州', 'BMWが関税リスクの中でも2026年見通しを維持したことは安心材料だったが、あくまで個社の耐久力を示しただけで、欧州の通商問題を解決したわけではない。', '<strong>なぜ限定的か：</strong>足元の実行力は株価を支えられても、関税が続けば利益率リスクは残る。市場が買ったのはマクロ改善ではなく企業の持久力だ。', [src['bmw'], src['eu_deadline']]),
        ('欧州', 'トランプ氏のEU向け7月4日期限は重い。企業が供給網を調整し切る前に、政策悪化を前提に計画を組まざるを得なくなるからだ。', '<strong>なぜ効くか：</strong>短い期限は投資先送り、在庫再編、現金防衛を早める。不確実性そのものが景気を冷やす。', [src['eu_deadline'], src['bmw']]),
        ('欧州', '欧州が中東ショックに弱いのは、もともと成長基盤が弱く、輸入インフレを吸収する余地が米国より小さいからだ。', '<strong>なぜ苦しいか：</strong>油高は家計にも産業にも同時に負担をかける。その痛みが、すでに弱い需要に上乗せされる。', [src['airlines'], src['hormuz_attack']]),
    ],
    'アジア（日本除く）': [
        ('アジア（日本除く）', 'インドの信用保証は、この日の最も明確な政策対応の一つだった。燃料ショックが雇用や中小企業金融へ広がる前に、運転資金を守るほうが安いと判断したからだ。', '<strong>なぜ先手が必要か：</strong>輸入エネルギー高は輸送、資金繰り、景況感を一気に傷つける。保証策はその連鎖を途中で止める狙いだ。', [src['india_credit'], src['airlines']]),
        ('アジア（日本除く）', 'ホルムズ海峡の海運リスクがアジアで重いのは、外交問題としてより先に、運賃、LNG、原油代として痛みが来るからだ。', '<strong>なぜ物流ショックか：</strong>地域は海上エネルギー輸送への依存度が高く、GDP統計より先に企業コストが動く。', [src['hormuz_attack'], src['india_credit']]),
        ('アジア（日本除く）', 'AI関連が旧来型景気株より強かったのは、計算資源と半導体が、油安や通商安定にあまり頼らない数少ない成長領域と見られているからだ。', '<strong>なぜ資金が集まるか：</strong>マクロが悪化すると、需要が見えやすく戦略支援もある分野へ資金が逃げ込む。その受け皿がAIだった。', [src['asia_ai']]),
    ],
    '中東・アフリカ': [
        ('中東・アフリカ', f'原油は依然としてマクロの中心で、WTIは{wti_level}（{wti_day}）、Brentは{brent_level}（{brent_day}）だった。海運混乱が在庫と保険コストを押し上げ続けると見られているからだ。', '<strong>なぜ高止まりするか：</strong>市場は単発の見出しではなく、混乱の長さを値付けしている。供給停止がなくても、迂回と予防在庫でショックは続く。', [src['hormuz_attack'], src['airlines']]),
        ('中東・アフリカ', '航空会社の見通し引き下げは、紛争が原油ニュースから旅行・物流の業績問題へ広がった証拠だ。', '<strong>なぜ業績問題か：</strong>航路延長で燃料消費が増え、保険料も上がり、運航効率も落ちる。この三重苦が今日のガイダンス修正につながった。', [src['airlines'], src['hormuz_attack']]),
        ('中東・アフリカ', '南ア中銀が選択肢を開いたままにしたのも重要だ。湾岸から遠い国でも、エネルギーリスクでインフレ姿勢を慎重化せざるを得ないからだ。', '<strong>なぜ金融政策に波及するか：</strong>輸入燃料高は利下げ余地を削る。紛争が商品市況から中央銀行の判断へ伝播している。', [src['sa_rate'], src['hormuz_attack']]),
    ],
    'ラテンアメリカ': [
        ('ラテンアメリカ', 'ルラ大統領がトランプ氏との会談に満足感を示したのは、関税政治がさらに硬化する前に、対米関係のリスクを少しでも下げたいからだ。', '<strong>なぜ今か：</strong>ブラジルは米国との接点と商品需要の両方を保ちたい。外交的な温度を上げること自体が外部環境悪化へのヘッジになる。', [src['lula']]),
        ('ラテンアメリカ', 'ベネズエラがより広い中南米の地経学リセットの入口として見られているのは、どの国が資本、制裁緩和、通商アクセスを得るかが変わり始めているからだ。', '<strong>なぜ一国問題ではないか：</strong>地政学で地域の序列が変わると、資金は一国だけでなく地域全体を再評価する。ベネズエラはその最初のシグナルだ。', [src['venezuela'], src['lula']]),
        ('ラテンアメリカ', 'メキシコが連邦事業で地場鉄鋼を求めたのは、米関税圧力が地域へ波及し、各国が独自の産業防衛を始めたからだ。', '<strong>なぜ連鎖するか：</strong>米通商政策が硬化すると、周辺国は国内生産者が痛みを丸かぶりしないよう防御に動く。二国間問題が地域の供給網再編へ変わる。', [src['mexico_steel'], src['argentina_risk']]),
    ],
    'オセアニア': [
        ('オセアニア', 'オセアニアは他地域ほど新しい見出しは多くなかったが、アジア向け海運コストが上がるほど、輸入依存の高い経済にはじわじわ効く。', '<strong>なぜ静かながら重要か：</strong>距離が長い地域ほど物流インフレが増幅される。ローカル見出しがなくても、中東由来の海運ストレスはコスト面で確実に伝わる。', [src['hormuz_attack'], src['airlines']]),
    ],
}

pred_en = [
    ('TOMORROW', 'Tomorrow’s first question is whether Tokyo turns today’s coordinated yen-defense language into a harder policy signal, because verbal support fades quickly if traders see no follow-through.', '<strong>Why to watch it:</strong> if officials move from messaging to action, exporters, JGBs, and Japanese bank stocks could all reprice together.'),
    ('WEEK AHEAD', 'The risk for the week ahead is that oil, yields, and tariffs stop behaving like separate headlines and start acting like one tightening machine.', '<strong>Why to watch it:</strong> once energy costs, funding pressure, and trade friction reinforce each other, earnings downgrades usually arrive with a lag, then all at once.'),
]

pred_ja = [
    ('明日', '明日の焦点は、東京が今日の円防衛メッセージをさらに強い政策シグナルへ変えるかどうかだ。言葉だけでは投機筋への効き目が長続きしにくいからだ。', '<strong>なぜ見るべきか：</strong>メッセージが実行へ進めば、輸出株、国債、銀行株が一斉に再評価されやすい。'),
    ('来週', '来週のリスクは、原油高、金利高、関税が別々の見出しではなく、一つの引き締め装置として効き始めることだ。', '<strong>なぜ重要か：</strong>エネルギー、資金コスト、通商摩擦が重なると、業績下方修正は遅れてから一気に出やすい。'),
]


def render_page(lang='en'):
    is_ja = lang == 'ja'
    edition_date = f'{TODAY_JA} 午後版' if is_ja else f'{TODAY_EN} — Afternoon Edition'
    edition_sub = (
        f'🇯🇵 The real afternoon shift was that Japan moved from tolerating yen weakness to preparing a multi-front defense, while the rest of the world kept absorbing the same oil, tariff, and yield squeeze · Health Score: {HEALTH}/100'
        if not is_ja else
        f'🇯🇵 午後の本当の変化は、日本が円安を受け流す段階から多面的な防衛準備へ移ったことだ。一方で世界は原油高、関税、金利高の圧力をなお吸収し続けた · Health Score: {HEALTH}/100'
    )
    nav = [('japan', '日本' if is_ja else 'Japan'), ('global', '世界' if is_ja else 'Global'), ('markets', '市場' if is_ja else 'Markets'), ('predictions', '予測' if is_ja else 'Predictions'), ('bottomline', '結論' if is_ja else 'Bottom Line')]
    jp_source = japan_ja if is_ja else japan_en
    gl_source = global_ja if is_ja else global_en
    pred_source = pred_ja if is_ja else pred_en
    jp_html = '\n'.join(story_card(*item, ja=is_ja) for item in jp_source)
    global_html = '\n'.join(story_card(*item, ja=is_ja) for region in gl_source.values() for item in region)
    markets = '\n'.join([
        table_card('株式' if is_ja else 'EQUITIES', '主要株価指数' if is_ja else 'End-of-day equity snapshot', ['指数' if is_ja else 'Index', '水準' if is_ja else 'Level', '日次' if is_ja else 'Daily', '週次' if is_ja else 'Weekly', '月次' if is_ja else 'Monthly', 'YTD'], EQ_ROWS, '<strong>大きな動きの理由：</strong>通常以上の変動は、原油高、金利高、関税圧力の三重苦で説明できる。日本はそれに円と政策正常化リスクが重なった。' if is_ja else '<strong>Why the bigger moves happened:</strong> anything beyond a routine move was still being driven by the same three-way squeeze, oil, yields, and tariff risk. Japan stayed more fragile because currency and policy normalization risk were layered on top.', [src['asia_ai'], src['us_japan_fx'], src['yahoo']]),
        table_card('為替・金利' if is_ja else 'FX & RATES', '為替・金利の要点' if is_ja else 'Currency and rate pressure points', ['項目' if is_ja else 'Instrument', '水準' if is_ja else 'Level', '日次' if is_ja else 'Daily', '週次' if is_ja else 'Weekly', '月次' if is_ja else 'Monthly', 'YTD'], FX_ROWS, f'<strong>なぜ重要か：</strong>USD/JPY {usdjpy_level} と米10年債 {us10_level}（{us10_day}）は、日本資産と世界の資金調達条件に直接効く、午後の最重要ストレス指標だった。' if is_ja else f'<strong>Why it matters:</strong> USD/JPY at {usdjpy_level} and the US 10-year at {us10_level} ({us10_day}) were the cleanest tightening gauges of the afternoon because they transmit policy stress directly into Japanese assets and global funding conditions.', [src['us_japan_fx'], src['boj_masu'], src['yahoo']]),
        table_card('商品・暗号資産' if is_ja else 'COMMODITIES & CRYPTO', '商品・暗号資産' if is_ja else 'Commodity and digital-asset close', ['資産' if is_ja else 'Asset', '価格' if is_ja else 'Price', '日次' if is_ja else 'Daily', '週次' if is_ja else 'Weekly', '月次' if is_ja else 'Monthly', 'YTD'], CMD_ROWS, f'<strong>大きな変動の因果：</strong>原油が強いのは供給不安が長引くと見られているからで、金 {gold_level}（{gold_day}）は安全資産需要があってもドル高と実質金利で上値を抑えられた。' if is_ja else f'<strong>Big mover logic:</strong> oil stayed bid because supply risk still looks persistent, while gold at {gold_level} ({gold_day}) had to fight a firmer dollar and higher real-rate pressure instead of enjoying a clean haven bid.', [src['hormuz_attack'], src['airlines'], src['yahoo']]),
        story_card('HEALTH SCORE', f'{HEALTH}/100, 日本は政策シグナルが明確になった一方で、世界全体は原油高、金利高、関税圧力でなお締まっているからだ。' if is_ja else f'{HEALTH}/100, because Japan gained some policy clarity but the global system kept tightening through oil, yields, and tariffs at the same time.', '<strong>なぜ58か：</strong>日本の輪郭は見えたが、世界のコスト圧力は弱まっていない。改善は局所的で、引き締まりは広域のままだ。' if is_ja else '<strong>Why 58:</strong> Japan reduced one uncertainty by showing more policy intent, but that did not offset the broader tightening impulse coming from energy, funding costs, and trade friction.', [src['us_japan_fx'], src['hormuz_attack'], src['airlines']], ja=is_ja, featured=False),
    ])
    pred_html = '\n'.join(story_card(tag, head, body, [src['us_japan_fx'], src['boj_masu']] if i == 0 else [src['hormuz_attack'], src['eu_deadline'], src['airlines']], ja=is_ja) for i, (tag, head, body) in enumerate(pred_source))
    bottom = 'The real afternoon change was that <strong>Japan stopped looking like a passive victim of yen weakness and started looking like a country preparing a coordinated defense across FX, rates, and corporate messaging.</strong> <strong>Bottom line:</strong> Tokyo looks readier to act, but the rest of the world still faces a tightening machine powered by oil, tariffs, and yields.' if not is_ja else '午後の本当の変化は、<strong>日本が円安の受け身の被害者ではなく、為替、金利、企業メッセージを組み合わせた防衛に動き始めたように見えたこと</strong>だ。<strong>結論：</strong>東京は動く構えを強めたが、世界全体では原油高、関税、金利高がなお一体となって締め付けている。'
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
<header class="masthead"><div class="lang-toggle"><a href="index.html" class="{'active' if not is_ja else ''}">EN</a><span class="sep">/</span><a href="ja.html" class="{'active' if is_ja else ''}">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{edition_date}</div><div class="edition-sub">{edition_sub}</div><div class="divider-bar"></div></div></header>
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
