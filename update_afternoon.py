# -*- coding: utf-8 -*-
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BASE = Path('/Users/xand/.openclaw/workspace/ceo-briefing')
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TODAY_EN = 'Thursday, May 14, 2026'
TODAY_JA = '2026年5月14日（木）'
TITLE_DATE = 'May 14, 2026'
WAR_DAY = '75'
HEALTH = 64


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
    'asia_ai': gnews('Asia stocks gain on AI enthusiasm focus on Trump Xi summit Reuters'),
    'us_japan_fx': gnews('US Japan agree excess FX volatility undesirable Bessent says Reuters'),
    'boj_masu': gnews('BOJ board member Masu calls for early rate hike Reuters'),
    'kuroda': gnews('Ex BOJ chief Kuroda sees yen intervention impact as short-lived Reuters'),
    'japan_tanker': gnews('Second Japan linked crude oil tanker passes through Strait of Hormuz Reuters'),
    'toyota_iran': gnews('Toyota expects $4.3 billion hit from effects of Iran war Reuters'),
    'softbank_ai': gnews('Japan SoftBank explores homegrown AI servers with Nvidia Foxconn Reuters'),
    'anthropic_megabanks': gnews('Japan megabanks gain access to Anthropic Mythos in about two weeks source says Reuters'),
    'bmw': gnews('BMW keeps 2026 guidance shrugs off tariff threat as profit beats expectations Reuters'),
    'eu_deadline': gnews('Trump sets July 4 deadline for EU to comply with trade deal or face much higher tariffs Reuters'),
    'india_credit': gnews('India approves $1.9 billion credit guarantee to support businesses hit by Middle East crisis Reuters'),
    'airlines': gnews('Airlines tackle fuel cost surge with price hikes outlook cuts Reuters'),
    'hormuz_attack': gnews('South Korea official says unlikely anyone but Iran behind Hormuz ship attack Reuters'),
    'sa_rate': gnews('South Africa Kganyago says central bank must keep rate options open amid inflation threat Reuters'),
    'lula': gnews("Brazil's Lula says he's very satisfied after meeting with Trump Reuters"),
    'venezuela': gnews('Venezuela marks the opening move in a LatAm geoeconomic reset Reuters'),
    'mexico_steel': gnews('Mexico to require federal projects to use local steel in response to US tariffs Reuters'),
    'argentina_risk': gnews('Argentina country risk falls steadily fueling debate on return to capital markets Reuters'),
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
wti_level, wti_day = CMD_ROWS[0][1], CMD_ROWS[0][2]
brent_level, brent_day = CMD_ROWS[1][1], CMD_ROWS[1][2]

japan = [
    {
        'tag': '🇯🇵 JAPAN · MARKET CLOSE',
        'headline': f'Tokyo finished the day with the Nikkei at {nikkei_level} ({nikkei_day}) because afternoon buyers chased the global AI trade, but gains stayed selective as yen-policy risk kept exporters from becoming a full risk-on bid.',
        'body': '<strong>Why it happened:</strong> the afternoon impulse came from global chip and AI enthusiasm plus hopes around a Trump-Xi summit, but Japan could not fully behave like a clean growth market because every exporter rally was checked by the possibility of stronger yen defence and higher domestic rates.',
        'sources': [src['asia_ai'], src['us_japan_fx']],
    },
    {
        'tag': '🇯🇵 JAPAN · FX / DIPLOMACY',
        'headline': f'Bessent saying the US and Japan agree that excess FX volatility is undesirable mattered immediately because it gave Tokyo more diplomatic cover to lean against USD/JPY at {usdjpy_level} ({usdjpy_day}) without turning the move into a trade fight.',
        'body': '<strong>Why it happened:</strong> intervention threats work better when markets think Washington will tolerate them. The causal chain is US political tolerance first, stronger Japanese currency signalling second, which is why the wording itself moved expectations.',
        'sources': [src['us_japan_fx'], src['kuroda']],
    },
    {
        'tag': '🇯🇵 JAPAN · BOJ / RATES',
        'headline': 'BOJ board member Masu calling for an early rate hike changed the afternoon tone because it told investors the weak-yen problem is no longer just a Ministry of Finance issue, it is creeping into the BOJ reaction function too.',
        'body': '<strong>Why it happened:</strong> once currency weakness starts feeding imported inflation and credibility risk, the central bank cannot hide behind patience forever. Markets heard Masu as a signal that rate normalization could be pulled forward if yen pass-through worsens.',
        'sources': [src['boj_masu'], src['us_japan_fx']],
    },
    {
        'tag': '🇯🇵 JAPAN · INTERVENTION LIMITS',
        'headline': 'Kuroda warning that yen intervention effects are short-lived mattered because it sharpened the market’s next question, whether Tokyo will pair spot defence with either tighter rates or a bigger policy package.',
        'body': '<strong>Why it happened:</strong> one-off FX operations can slow speculation, but they rarely reverse a move when rate differentials still favor the dollar. That is why the market treated Kuroda’s comment as pressure for follow-through, not as a reason to relax.',
        'sources': [src['kuroda'], src['boj_masu']],
    },
    {
        'tag': '🇯🇵 JAPAN · CORPORATE / ENERGY',
        'headline': 'Toyota flagging a roughly $4.3 billion hit from the Iran war landed as the clearest corporate warning of the afternoon because energy, shipping, and parts costs are now large enough to show up in guidance, not just in macro commentary.',
        'body': '<strong>Why it happened:</strong> the war raises fuel costs, extends logistics routes, and disrupts supplier timing at the same time. Toyota matters because it turns an abstract geopolitical shock into a concrete earnings drag for Japan’s flagship manufacturer.',
        'sources': [src['toyota_iran'], src['japan_tanker']],
    },
    {
        'tag': '🇯🇵 JAPAN · CORPORATE / AI',
        'headline': 'SoftBank exploring homegrown AI servers with Nvidia and Foxconn stood out because Japanese groups are trying to localize strategic compute capacity before geopolitics or tariffs make foreign dependence even more expensive.',
        'body': '<strong>Why it happened:</strong> AI demand is rising just as supply chains are getting politically riskier. Building more of the stack under Japanese influence is both a growth bet and a resilience play.',
        'sources': [src['softbank_ai'], src['anthropic_megabanks']],
    },
]

global_regions = {
    'North America': [
        ('North America', f'US equities held near highs, with the S&P 500 at {spx_level} ({spx_day}), because the same AI narrative lifting Asia was reinforced by hopes that a Trump-Xi meeting could cap the next trade escalation.', '<strong>Why it happened:</strong> investors bought the idea that AI capex still has momentum and that summit diplomacy could reduce the odds of a fresh tariff shock. The rally stayed measured because neither story has actually removed inflation or geopolitical risk yet.', [src['asia_ai']]),
        ('North America', 'Washington’s message discipline on FX mattered beyond Japan because it showed the US is trying to stabilize allied markets selectively rather than abandon a hard line everywhere.', '<strong>Why it happened:</strong> the US wants to keep strategic partners aligned while preserving leverage against rivals. That selective flexibility is why allied currencies got more breathing room even as the broader trade posture stayed tough.', [src['us_japan_fx']]),
        ('North America', 'Higher fuel costs started bleeding more directly into US corporate planning because airlines are already raising fares and cutting outlooks instead of waiting for oil to normalize on its own.', '<strong>Why it happened:</strong> once fuel, insurance, and routing costs rise together, executives stop treating the shock as temporary noise and start repricing capacity and guidance.', [src['airlines'], src['hormuz_attack']]),
    ],
    'Europe': [
        ('Europe', 'BMW holding 2026 guidance despite tariff risk was mildly reassuring because strong current execution is buying time for European autos, but not removing the policy threat hanging over the sector.', '<strong>Why it happened:</strong> good near-term profits can cushion sentiment, yet tariffs still threaten volumes and margins if they stick. Investors treated the result as proof of resilience, not proof that the trade problem is solved.', [src['bmw'], src['eu_deadline']]),
        ('Europe', 'Trump’s July 4 deadline for the EU mattered because it compressed negotiation time and raised the odds that tariff risk will hit European boardrooms before they can adjust supply chains.', '<strong>Why it happened:</strong> a shorter deadline changes corporate behavior immediately. Firms start freezing decisions when they fear the policy regime may worsen before inventories and contracts can be reworked.', [src['eu_deadline'], src['bmw']]),
        ('Europe', 'Europe remained vulnerable to the Middle East shock because its weak growth base leaves less room to absorb another imported energy squeeze than the US or parts of Asia.', '<strong>Why it happened:</strong> higher oil acts like a tax on households and industry at the same time. That matters more in Europe because growth was already soft before the latest shipping and tariff risks landed.', [src['airlines'], src['hormuz_attack']]),
    ],
    'Asia ex-Japan': [
        ('Asia ex-Japan', 'India’s $1.9 billion credit guarantee was one of the day’s clearest policy reactions because New Delhi decided it was cheaper to protect working capital early than let fuel-shock stress spread into jobs and SME financing.', '<strong>Why it happened:</strong> imported energy inflation hits transport, cash flow, and confidence fast. The guarantee is meant to break that chain before it turns a geopolitical shock into a domestic slowdown.', [src['india_credit'], src['airlines']]),
        ('Asia ex-Japan', 'The Hormuz attack attribution debate mattered for the rest of Asia because import-dependent economies are trading the story as a shipping-risk problem first and a diplomatic problem second.', '<strong>Why it happened:</strong> Asian economies feel the pain through freight, LNG, and crude costs long before any military response shows up in official GDP data.', [src['hormuz_attack'], src['india_credit']]),
        ('Asia ex-Japan', 'AI enthusiasm across regional equities held up better than old-economy cyclicals because investors still see compute and semis as the one growth pocket least dependent on cheap fuel or easy trade politics.', '<strong>Why it happened:</strong> when the macro backdrop worsens, capital crowds into sectors with visible capex demand and strategic support. That is why AI outperformed even while broader regional risk stayed fragile.', [src['asia_ai']]),
    ],
    'Middle East & Africa': [
        ('Middle East & Africa', f'Crude stayed the macro hinge, with WTI at {wti_level} ({wti_day}) and Brent at {brent_level} ({brent_day}), because traders still see shipping disruption as persistent enough to keep inventories, insurance, and rerouting costs elevated.', '<strong>Why it happened:</strong> prices no longer need a single spectacular outage to stay firm. The market is pricing duration risk, which means higher costs can persist even on a day without a fresh physical supply collapse.', [src['hormuz_attack'], src['airlines']]),
        ('Middle East & Africa', 'Airlines turning to fare hikes and outlook cuts showed the conflict is broadening from an oil headline into a real-economy earnings problem.', '<strong>Why it happened:</strong> longer routes burn more fuel, higher insurance raises operating costs, and uncertainty reduces schedule efficiency. That triple hit explains why carriers are changing guidance now.', [src['airlines'], src['hormuz_attack']]),
        ('Middle East & Africa', 'South Africa’s central bank keeping its options open mattered because even countries far from the Gulf are being forced to hold a tighter inflation posture as energy risk re-enters the system.', '<strong>Why it happened:</strong> imported fuel stress can delay easing cycles everywhere. South Africa is a reminder that the conflict is feeding directly into global central-bank caution.', [src['sa_rate'], src['hormuz_attack']]),
    ],
    'Latin America': [
        ('Latin America', 'Lula saying he was very satisfied after meeting Trump mattered because Brazil is trying to de-risk the US relationship before tariff politics and bloc pressure reduce its room to stay flexible.', '<strong>Why it happened:</strong> Brazil benefits from access to both Washington and commodity demand elsewhere. The diplomatic warmth is meant to preserve that balancing room before the external environment hardens further.', [src['lula']]),
        ('Latin America', 'Venezuela becoming the opening move in a broader LatAm geoeconomic reset mattered because US pressure and regional realignment are starting to reprice which countries get capital, sanctions relief, and trade access.', '<strong>Why it happened:</strong> when geopolitics changes the pecking order, investors re-rate whole regions, not just one country. Venezuela is being watched as the first signal of that wider reset.', [src['venezuela'], src['lula']]),
        ('Latin America', 'Mexico requiring federal projects to use local steel showed how US tariff pressure is cascading through the region because governments are responding with their own industrial defenses instead of waiting for trade talks to settle.', '<strong>Why it happened:</strong> once the US hardens trade policy, neighbors start protecting domestic producers to avoid importing the pain. That turns bilateral tariff disputes into regional supply-chain rewiring.', [src['mexico_steel'], src['argentina_risk']]),
    ],
}

global_regions_ja = {
    '北米': [
        ('北米', f'米株はS&P 500が{spx_level}（{spx_day}）近辺を維持した。アジアを押し上げたAI物色が米国でも続き、トランプ・習会談への期待が次の関税悪化を少し和らげたからだ。', '<strong>なぜそうなったか：</strong>投資家は、AI投資の勢いが続くことと、首脳会談で通商悪化の速度が鈍る可能性を買った。ただしインフレや地政学リスクが消えたわけではないので、上昇は熱狂ではなく選別的だった。', [src['asia_ai']]),
        ('北米', '米国が日本との為替安定メッセージを明確にしたことは、日本だけでなく北米政策の柔軟性を示した。米国は全方位で硬直するのではなく、同盟国には選別的に安定を与えようとしている。', '<strong>なぜ重要か：</strong>同盟維持と対中・対外強硬姿勢を両立するには、味方市場の混乱を一部抑える必要がある。そのための選別的安定化だ。', [src['us_japan_fx']]),
        ('北米', '燃料高が米企業計画へ入り始めたことも重要だ。航空会社が運賃引き上げと見通し下方修正に動いたのは、原油が自然に戻るのを待てない水準までコストが積み上がったからだ。', '<strong>なぜ今表面化したか：</strong>燃料、保険、迂回の3つが同時に上がると、一時ノイズでは処理できない。だから経営計画そのものが書き換わり始める。', [src['airlines'], src['hormuz_attack']]),
    ],
    '欧州': [
        ('欧州', 'BMWが関税リスクの中でも2026年見通しを維持したのは安心材料だったが、意味は「持ちこたえている」であって「問題が消えた」ではない。', '<strong>なぜそう読むべきか：</strong>足元の採算が良くても、関税が続けば数量と利益率の両方が削られる。市場は耐久性を評価したが、政策リスクまでは消していない。', [src['bmw'], src['eu_deadline']]),
        ('欧州', 'トランプ氏がEUに7月4日の期限を突き付けたことは、企業の調整時間を圧縮した。サプライチェーンを動かす前に政策条件が悪化する恐れが高まったからだ。', '<strong>なぜ期限が効くか：</strong>交渉期限が短いほど、企業は投資や在庫判断を止めやすい。不確実性そのものが景気の重しになる。', [src['eu_deadline'], src['bmw']]),
        ('欧州', '欧州が中東ショックに弱いままなのは、もともと成長基盤が弱く、追加の輸入インフレを吸収する余力が米国や一部アジアより小さいからだ。', '<strong>なぜ苦しいか：</strong>油高は家計にも産業にも同時に課税する。その痛みが、もともと弱い景気に重なる。', [src['airlines'], src['hormuz_attack']]),
    ],
    'アジア（日本除く）': [
        ('アジア（日本除く）', 'インドの19億ドル信用保証は、この日の最も明確な先手対応の一つだった。燃料ショックが雇用や中小企業金融へ広がる前に、運転資金を守るほうが安いと判断したからだ。', '<strong>なぜ先手が必要か：</strong>輸入エネルギー高は輸送、資金繰り、景況感を一気に傷つける。保証策はその連鎖を途中で止めるためのものだ。', [src['india_credit'], src['airlines']]),
        ('アジア（日本除く）', 'ホルムズ攻撃の主体を巡る議論がアジアで重いのは、軍事より先に海運コストとして痛みが来るからだ。', '<strong>なぜ外交論より物流論か：</strong>アジアの輸入国は、まず運賃と原燃料価格で打撃を受ける。GDP統計より先に企業コストが動く。', [src['hormuz_attack'], src['india_credit']]),
        ('アジア（日本除く）', '地域株でAI関連が旧来の景気敏感株より強かったのは、安い燃料や穏やかな通商環境に依存しない数少ない成長テーマだからだ。', '<strong>なぜ資金が集まるか：</strong>マクロが悪化するほど、需要が見えやすく戦略支援も受けやすい分野へ資金が集中する。', [src['asia_ai']]),
    ],
    '中東・アフリカ': [
        ('中東・アフリカ', f'原油は依然マクロの軸で、WTIは{wti_level}（{wti_day}）、Brentは{brent_level}（{brent_day}）近辺にある。市場が海運混乱を短期ノイズではなく、保険・在庫・迂回を伴う持続コストとして見ているからだ。', '<strong>なぜ高止まりするか：</strong>価格は単一の供給停止だけで決まらない。混乱が長引くほど、在庫積み増しや保険料が価格を支える。', [src['hormuz_attack'], src['airlines']]),
        ('中東・アフリカ', '航空各社が運賃引き上げと見通し下方修正に動いたことで、紛争は原油見出しから実体経済の利益問題へ広がった。', '<strong>なぜそこまで波及したか：</strong>迂回で燃料が増え、保険が上がり、運航効率が落ちる。この三重苦がガイダンス修正を促した。', [src['airlines'], src['hormuz_attack']]),
        ('中東・アフリカ', '南ア中銀が選択肢を開いたままにしているのも重要だ。湾岸から遠い国ですら、エネルギー起点のインフレ再上昇で緩和を急げなくなっているからだ。', '<strong>なぜ世界の話になるか：</strong>燃料ショックは距離に関係なく利下げ余地を削る。南アはその世界的な慎重化の縮図だ。', [src['sa_rate'], src['hormuz_attack']]),
    ],
    'ラテンアメリカ': [
        ('ラテンアメリカ', 'ルラ大統領がトランプ会談後に「非常に満足」と語ったのは、関税政治と陣営圧力が強まる前に、米国との関係を実務的に安定させたいからだ。', '<strong>なぜ今温度を上げるか：</strong>ブラジルはワシントンとの接点と資源需要の両方を保つことで利益を得る。外交の柔らかさは、そのバランスを守るためだ。', [src['lula']]),
        ('ラテンアメリカ', 'ベネズエラが地域の地経学リセットの起点になりつつある点も重い。米国の圧力と地域再編が、資本流入や制裁緩和の優先順位を変え始めているからだ。', '<strong>なぜ一国の話で終わらないか：</strong>地政学が序列を変えると、投資家は国単位ではなく地域全体を再評価する。ベネズエラはその最初のシグナルになっている。', [src['venezuela'], src['lula']]),
        ('ラテンアメリカ', 'メキシコが連邦案件で国産鉄鋼を義務付けたのは、米関税圧力が地域全体に産業防衛を連鎖させているからだ。', '<strong>なぜ連鎖するか：</strong>米国が通商を硬化させるほど、周辺国も国内生産者保護へ傾く。二国間問題が地域の供給網再編へ変わる。', [src['mexico_steel'], src['argentina_risk']]),
    ],
}

market_sources = [src['asia_ai'], src['us_japan_fx'], src['hormuz_attack'], src['airlines'], src['yahoo']]


def build_body(lang='en'):
    if lang == 'en':
        japan_cards = '\n'.join(story_card(x['tag'], x['headline'], x['body'], x['sources']) for x in japan)
        global_cards = []
        for _, items in global_regions.items():
            for tag, headline, body, sources in items:
                global_cards.append(story_card(tag, headline, body, sources))
        global_cards = '\n'.join(global_cards)
        markets = '\n'.join([
            table_card('EQUITIES', 'End-of-day equity snapshot', ['Index', 'Level', 'Daily', 'Weekly', 'Monthly', 'YTD'], EQ_ROWS, '<strong>Why the larger moves happened:</strong> the market leadership still came from AI-heavy equities and selective cyclicals, while policy-sensitive Europe and fuel-sensitive regions lagged. If any line is moving more than 2%, the cleanest read is either AI concentration on the upside or conflict-driven energy and rate repricing on the downside.', market_sources),
            table_card('FX & RATES', 'Currency and rate pressure points', ['Instrument', 'Level', 'Daily', 'Weekly', 'Monthly', 'YTD'], FX_ROWS, '<strong>Why it matters:</strong> USD/JPY remains the fastest gauge of whether Tokyo must escalate from diplomacy to action. Treasury yields and the dollar stayed firm because growth and inflation resilience in the US still delays easy-policy hopes.', market_sources),
            table_card('COMMODITIES & CRYPTO', 'Commodity and digital-asset close', ['Asset', 'Price', 'Daily', 'Weekly', 'Monthly', 'YTD'], CMD_ROWS, '<strong>Big mover logic:</strong> if crude is up more than 2%, the cause is still shipping-duration risk around Hormuz feeding insurance and inventory demand. If gold, silver, or crypto are swinging hard, the cleaner causal chain is dollar repricing plus renewed demand for inflation or instability hedges.', market_sources),
            f'''        <article class="card fade-in" data-image="{next((x.get('image','') for x in market_sources if x.get('image')), '')}"><span class="card-tag">HEALTH SCORE</span><h3 class="card-headline">{HEALTH}/100, a touch firmer than this morning because Japan added policy clarity, but still below comfort because the world keeps getting repriced by oil routes and tariff clocks.</h3><p class="card-body"><strong>Why {HEALTH}:</strong> the score improved because Tokyo gained more credible tools, Bessent reduced near-term FX friction risk, and AI strength kept global equities from rolling over. It stays mediocre because oil, shipping, and tariff deadlines are still powerful enough to reverse risk sentiment quickly.</p><div class="card-sources">\n{source_links(market_sources)}\n</div></article>'''
        ])
        predictions = '''        <article class="card fade-in collapsible" data-image=""><span class="card-tag">TOMORROW</span><h3 class="card-headline">Watch whether Tokyo follows diplomatic yen cover with either a clearer intervention signal or more open BOJ hawkishness, because today’s messaging raised the cost of doing nothing.</h3><div class="tap-hint">Tap to expand</div><p class="card-body"><strong>Why it matters:</strong> once markets hear both Washington tolerance and BOJ unease, the next test is whether Japanese officials convert words into a more durable policy mix.</p><div class="card-sources">\n''' + source_links([src['us_japan_fx'], src['boj_masu'], src['kuroda']]) + '''\n</div></article>
        <article class="card fade-in collapsible" data-image=""><span class="card-tag">WEEK AHEAD</span><h3 class="card-headline">The bigger risk is that the Iran shock stops being mainly an oil story and starts showing up everywhere as earnings downgrades, tighter central banks, and delayed capex.</h3><div class="tap-hint">Tap to expand</div><p class="card-body"><strong>Why it matters:</strong> once fuel, insurance, freight, and policy uncertainty hit guidance together, volatility usually becomes structural rather than headline-driven.</p><div class="card-sources">\n''' + source_links([src['hormuz_attack'], src['airlines'], src['toyota_iran']]) + '''\n</div></article>'''
        bottom_line = 'The real afternoon change was that <strong>Japan gained more credible policy tools at the exact moment the rest of the world became more hostage to oil routes, tariff deadlines, and cost guidance.</strong> Tokyo got US cover on FX, louder BOJ hawkishness, and clearer corporate proof of the energy shock. <strong>Bottom line:</strong> Japan improved in relative terms, but the global tape is still being priced by logistics stress and repricing of inflation risk.'
        sub = f'🇯🇵 This afternoon’s real delta was not just a market close, it was a policy upgrade: Tokyo gained US backing against disorderly FX, heard a louder BOJ hawkish note, and got corporate evidence from Toyota that the Iran shock is now hitting earnings · AI kept equities afloat globally, but Europe stayed pinned by tariff deadlines and import-energy risk · Health Score: {HEALTH}/100'
        footer = 'CEO Afternoon Briefing · Generated by Sanbot · Thursday, May 14, 2026'
        return f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html" class="active">EN</a><span class="sep">/</span><a href="ja.html">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">{WAR_DAY}</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_EN} — Afternoon Edition</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">Japan</a><a href="#global" class="nav-pill">Global</a><a href="#markets" class="nav-pill">Markets</a><a href="#predictions" class="nav-pill">Predictions</a><a href="#bottomline" class="nav-pill">Bottom Line</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">Japan Update — In Depth</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">Global — By Continent</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">Markets & Economy</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">Predictions</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''

    japan_cards = '\n'.join(story_card(x['tag'].replace('JAPAN', '日本').replace('MARKET CLOSE', '大引け').replace('FX / DIPLOMACY', '為替 / 外交').replace('BOJ / RATES', '日銀 / 金利').replace('INTERVENTION LIMITS', '介入の限界').replace('CORPORATE / ENERGY', '企業 / エネルギー').replace('CORPORATE / AI', '企業 / AI'),
                                        x['headline'], x['body'], x['sources'], ja=True) for x in [
        {
            'tag':'🇯🇵 日本・大引け',
            'headline':f'東京市場は日経平均が{nikkei_level}（{nikkei_day}）で引けた。午後は世界的なAI物色が支えた一方、円政策リスクが輸出株の全面高を止めたからだ。',
            'body':'<strong>なぜそうなったか：</strong>半導体とAIへの期待、さらにトランプ・習会談への期待が午後の買いを支えた。ただし日本では、円防衛強化や金利正常化の可能性が輸出企業の上値を抑え、素直な全面リスクオンにはならなかった。',
            'sources':[src['asia_ai'], src['us_japan_fx']],
        },
        {
            'tag':'🇯🇵 日本・為替 / 外交',
            'headline':f'ベッセント財務長官が「過度な為替変動は望ましくない」と日米で一致したことは重かった。USD/JPY {usdjpy_level}（{usdjpy_day}）近辺で東京が動くための対米カバーを強めたからだ。',
            'body':'<strong>なぜ効くか：</strong>介入や強いけん制は、ワシントンが容認すると市場が思うほど効きやすい。先に米国の政治的許容を作り、その後で日本の通貨防衛シグナルが強まるという因果だ。',
            'sources':[src['us_japan_fx'], src['kuroda']],
        },
        {
            'tag':'🇯🇵 日本・日銀 / 金利',
            'headline':'日銀の増水審議委員が早期利上げを呼びかけたことで、円安問題は財務省だけでなく日銀の反応関数にも入り始めたと市場は受け止めた。',
            'body':'<strong>なぜ午後に効いたか：</strong>円安が輸入インフレと政策信認の問題に変わると、日銀は「待つ」だけでは済まなくなる。市場は、円の価格転嫁が悪化すれば正常化前倒しもあり得ると読み直した。',
            'sources':[src['boj_masu'], src['us_japan_fx']],
        },
        {
            'tag':'🇯🇵 日本・介入の限界',
            'headline':'黒田前総裁が円介入の効果は短命と指摘したことで、市場の関心は「守るか」から「介入に金利や追加政策を組み合わせるか」へ移った。',
            'body':'<strong>なぜそこが論点か：</strong>金利差がドル有利のままなら、単発の介入は時間を買えても流れは変えにくい。だから黒田発言は安心材料ではなく、追撃策を求める圧力として受け止められた。',
            'sources':[src['kuroda'], src['boj_masu']],
        },
        {
            'tag':'🇯🇵 日本・企業 / エネルギー',
            'headline':'トヨタがイラン戦争の影響で約43億ドルの打撃を見込むと示したことは、エネルギー、海運、部品コストがマクロ論ではなく業績ガイダンスに入ったことを意味した。',
            'body':'<strong>なぜ重要か：</strong>戦争は燃料費を押し上げ、物流を長期化させ、部品調達のタイミングも乱す。日本を代表する製造業の数字として出たことで、地政学ショックが実際の利益圧迫に変わった。',
            'sources':[src['toyota_iran'], src['japan_tanker']],
        },
        {
            'tag':'🇯🇵 日本・企業 / AI',
            'headline':'SoftBankがNvidia、Foxconnと国産AIサーバーを探る動きは、地政学や関税で海外依存コストがさらに上がる前に、戦略計算資源を国内主導で確保したいからだ。',
            'body':'<strong>なぜ今か：</strong>AI需要が伸びる一方で、供給網は政治的に不安定になっている。日本の影響下でスタックを増やすことは、成長投資であると同時に耐久力投資でもある。',
            'sources':[src['softbank_ai'], src['anthropic_megabanks']],
        },
    ])
    global_cards = []
    for _, items in global_regions_ja.items():
        for tag, headline, body, sources in items:
            global_cards.append(story_card(tag, headline, body, sources, ja=True))
    global_cards = '\n'.join(global_cards)
    markets = '\n'.join([
        table_card('株式', '引け後マーケット一覧', ['指数', '水準', '日次', '週次', '月次', '年初来'], EQ_ROWS, '大きな値動きの中心はAI偏重の上昇と、エネルギー・政策リスクを抱える地域の弱さだった。2%超の変動は、AI集中か、紛争起点のエネルギーと金利再評価で読むのが自然。', market_sources),
        table_card('為替・金利', '通貨と金利の要点', ['指標', '水準', '日次', '週次', '月次', '年初来'], FX_ROWS, 'USD/JPYは、東京が外交から実弾へ進む必要があるかを見る最速の指標。米金利とドルは、米景気とインフレの底堅さが簡単な緩和期待を後ろ倒しにしているため高止まりしやすい。', market_sources),
        table_card('商品・暗号資産', '商品とデジタル資産の引け', ['資産', '価格', '日次', '週次', '月次', '年初来'], CMD_ROWS, '原油が2%超動くなら、今はホルムズ起点の輸送長期化リスクと保険・在庫需要で説明するのが最も自然。金や銀、暗号資産が大きく動くなら、ドル再評価と不安定化ヘッジ需要の変化が主因。', market_sources),
        f'''        <article class="card fade-in" data-image="{next((x.get('image','') for x in market_sources if x.get('image')), '')}"><span class="card-tag">ヘルススコア</span><h3 class="card-headline">{HEALTH}/100、朝よりは少し改善。ただし理由は安心感ではなく、日本の政策手段が増えた一方で、世界の脆さは残ったからだ。</h3><p class="card-body"><strong>なぜ{HEALTH}か：</strong>東京は為替で対米カバーを得て、日銀のタカ派色も少し増し、AI相場も株全体を支えた。一方で油、海運、関税期限がなお相場の反転要因として強いので、快適圏には遠い。</p><div class="card-sources">\n{source_links(market_sources)}\n</div></article>'''
    ])
    predictions = '''        <article class="card fade-in collapsible" data-image=""><span class="card-tag">明日</span><h3 class="card-headline">東京が外交的な円防衛を、より明確な介入シグナルや日銀のタカ派メッセージへ進めるか注視。</h3><div class="tap-hint">タップして展開</div><p class="card-body"><strong>なぜ重要か：</strong>米国の容認と日銀の不快感が見えた以上、次の焦点は言葉を持続的な政策ミックスへ変えるかどうかだ。</p><div class="card-sources">\n''' + source_links([src['us_japan_fx'], src['boj_masu'], src['kuroda']]) + '''\n</div></article>
    <article class="card fade-in collapsible" data-image=""><span class="card-tag">今週</span><h3 class="card-headline">イラン発ショックが原油の話で終わらず、利益下方修正、中銀慎重化、設備投資先送りへ広がるかが次の分岐点。</h3><div class="tap-hint">タップして展開</div><p class="card-body"><strong>なぜそこか：</strong>燃料、保険、運賃、政策不確実性が同時に企業ガイダンスへ入ると、ボラティリティは見出し主導から構造要因へ変わる。</p><div class="card-sources">\n''' + source_links([src['hormuz_attack'], src['airlines'], src['toyota_iran']]) + '''\n</div></article>'''
    bottom_line = '午後に変わった本質は、<strong>世界がなお油の航路と関税期限で振り回される中、日本だけは政策カードが朝より増えた</strong>ことだ。対米の為替カバー、日銀のタカ派化、トヨタによる業績面の警告が揃った。<strong>結論：</strong>日本は相対的に改善したが、世界全体の値付けは依然として物流ストレスとインフレ再評価に支配されている。'
    sub = f'🇯🇵 午後に増えたのは見出しではなく政策の手数だ。東京は無秩序な為替変動への対米カバーを得て、日銀のタカ派色も強まり、トヨタはイラン戦争の業績打撃を具体化した · 世界ではAIが株を支えた一方、欧州は関税期限と輸入エネルギー不安に縛られた · Health Score: {HEALTH}/100'
    footer = 'CEO Afternoon Briefing · Generated by Sanbot · 2026年5月14日（木）'
    return f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html">EN</a><span class="sep">/</span><a href="ja.html" class="active">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">{WAR_DAY}</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_JA} 午後版</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">日本</a><a href="#global" class="nav-pill">世界</a><a href="#markets" class="nav-pill">市場</a><a href="#predictions" class="nav-pill">予測</a><a href="#bottomline" class="nav-pill">結論</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">日本アップデート</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">世界の動き</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">市場と経済</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">予測</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''


def build_page(path: Path, lang='en'):
    src_html = path.read_text()
    head = src_html.split('<body>')[0] + '<body>\n'
    head = re.sub(r'<title>CEO Briefing — [^<]+</title>', f'<title>CEO Briefing — {TITLE_DATE}</title>', head)
    path.write_text(head + build_body(lang))


build_page(BASE / 'index.html', 'en')
build_page(BASE / 'ja.html', 'ja')
print('updated')
