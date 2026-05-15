from __future__ import annotations

import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BASE = Path('/Users/xand/.openclaw/workspace/ceo-briefing')
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TODAY_EN = 'Friday, May 15, 2026'
TODAY_JA = '2026年5月15日（金）'
TITLE_DATE = 'May 15, 2026'
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
        return {'url': link, 'source': source, 'title': item.findtext('title') or query, 'image': og_image(link)}
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
    return '\n'.join(
        f'            <a class="source-link" href="{item["url"]}" target="_blank" rel="noopener">{html.escape(item["source"])} <span class="src-arrow">↗</span></a>'
        for item in items if item.get('url')
    )


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


def story_card(tag, headline, body, sources, ja=False):
    image = next((x.get('image', '') for x in sources if x.get('image')), '')
    tap = 'タップして展開' if ja else 'Tap to expand'
    japan_cls = ' japan' if ('🇯🇵' in tag or '日本' in tag) else ''
    return f'''        <article class="card featured fade-in collapsible" data-image="{image}">
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
    'boj_poll': gnews('BOJ expected to raise rates to 1.0% in June hike again October December Reuters when:1d'),
    'japan_wpi': gnews("Japan wholesale inflation spikes on energy shock bolsters case for June rate hike Reuters when:1d"),
    'japan_prices': gnews('Japan may face more price hikes for food hot spring facilities central bank says Reuters when:1d'),
    'japan_summit': gnews('South Korea Japan summit Andong Reuters when:1d'),
    'asia_stocks': gnews('Asian shares dive as US yields hit one-year high Reuters when:1d'),
    'wallstreet': gnews('Wall Street ends higher on tech rally investors eye Beijing talks Reuters when:1d'),
    'yield_surge': gnews('Yield surge spoils the equity party Reuters when:1d'),
    'carry_fx': gnews('Carry on trading rate-based G10 currency bets make a comeback Reuters when:1d'),
    'europe_shares': gnews('European shares end at one-week highs on tech boost Reuters when:1d'),
    'europe_earnings': gnews('European blue-chip earnings set for strongest growth since late 2022 Reuters when:1d'),
    'airlines': gnews('Airlines cancel flights in response to Middle East conflict Reuters when:1d'),
    'oil': gnews('Oil rises after Trump says he is losing patience with Iran Reuters when:1d'),
    'india_credit': gnews('India approves $1.9 billion credit guarantee to support businesses hit by Middle East crisis Reuters when:1d'),
    'iraq': gnews('Iraq seeking financial assistance from IMF World Bank as result of Iran war Reuters when:1d'),
    'morocco': gnews('Morocco to add $2 billion to budget to soften economic impact of Middle East conflict Reuters when:1d'),
    'kenya': gnews('Kenya raises retail prices for fuel due to Iran conflict Reuters when:1d'),
    'cuba': gnews("Cuba mulls US offer of $100 million in aid but wary of Trump's motives blockade Reuters when:1d"),
    'peru': gnews("Peru's central bank holds benchmark interest rate at 4.25% Reuters when:1d"),
    'latam_commodities': gnews("New models needed to track China's messy commodity transition Reuters when:1d"),
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

japan_en = [
    ('🇯🇵 JAPAN · MARKET CLOSE', f'Tokyo finished with the Nikkei at {nikkei_level} ({nikkei_day}) because hotter US yields pushed global duration risk higher, while exporters found only partial relief from a still-weak yen at USD/JPY {usdjpy_level} ({usdjpy_day}).', '<strong>Why it happened:</strong> the causal chain ran from firmer US data to higher Treasury yields, from higher yields to tighter global financial conditions, and then into Japan where rate-sensitive names and duration plays underperformed even though the softer yen still cushions overseas earners.', [src['asia_stocks'], src['carry_fx']]),
    ('🇯🇵 JAPAN · INFLATION', 'Japan’s wholesale inflation spike became the afternoon’s most important domestic macro update because the energy shock is now feeding producer prices directly, which gives the BOJ a clearer reason to tighten earlier.', '<strong>Why it happened:</strong> imported fuel and utility costs rose after the Middle East conflict lifted shipping and energy prices, and that pass-through hit factory-gate prices fast enough to strengthen the June-hike case.', [src['japan_wpi'], src['oil']]),
    ('🇯🇵 JAPAN · BOJ', 'A Reuters poll showing the BOJ is expected to raise rates to 1.0% in June mattered because investors no longer see today’s inflation pressure as a one-off, they see it as the trigger for a faster normalization path.', '<strong>Why it happened:</strong> once wholesale inflation accelerates and the yen stays weak, the BOJ faces a credibility problem if it waits too long. That is why rate expectations firmed further this afternoon.', [src['boj_poll'], src['japan_wpi']]),
    ('🇯🇵 JAPAN · CONSUMER PRESSURE', 'The BOJ warning that more food and hot-spring price hikes may still be ahead matters politically because energy and rice costs are now hitting everyday categories that households notice immediately.', '<strong>Why it happened:</strong> electricity, gas, transport and agricultural inputs all rose together, so businesses that had delayed price moves are now being forced to pass them on. The political risk rises when inflation stops feeling abstract and starts showing up in dinner and leisure bills.', [src['japan_prices'], src['japan_wpi']]),
    ('🇯🇵 JAPAN · DIPLOMACY', 'The Lee-Takaichi summit set for May 19-20 is more than calendar filler because Tokyo and Seoul both want tighter coordination before the next round of regional security and trade stress.', '<strong>Why it happened:</strong> North Asia is dealing simultaneously with US-China bargaining, energy-route instability, and supply-chain security. That pressure is pushing allies to close gaps now rather than after another shock hits.', [src['japan_summit'], src['asia_stocks']]),
    ('🇯🇵 JAPAN · STRATEGY', 'Japan’s multi-billion-dollar chip push stayed in focus this afternoon because policymakers increasingly see domestic semiconductor capacity as insurance against a world of higher tariffs, export controls, and rerouted trade.', '<strong>Why it happened:</strong> when funding costs rise and geopolitics worsens, private capital alone will not build enough strategic capacity fast enough. That is why Tokyo keeps leaning on subsidies and industrial policy.', [gnews("Japan's $25 bln chip gambit is worth the wager Reuters when:1d"), src['asia_stocks']]),
]

global_en = {
    'North America': [
        ('North America', f'Wall Street still closed higher, with the S&P 500 at {spx_level} ({spx_day}), because tech buying beat out macro nerves as investors chose to focus on AI earnings power and the prospect of Beijing talks.', '<strong>Why it happened:</strong> mega-cap tech kept attracting money because its cash-flow story looks sturdier than the rest of the market, and hopes for talks with Beijing reduced the immediate fear of another tariff escalation.', [src['wallstreet']]),
        ('North America', f'US yields remained the real pressure point, with the 10-year at {us10_level} ({us10_day}), because stronger data kept pushing back the timeline for easier Fed policy.', '<strong>Why it happened:</strong> when growth and spending refuse to cool, bond investors demand higher compensation for holding duration. That rise in yields then tightens financial conditions everywhere else.', [src['yield_surge']]),
        ('North America', f'The dollar stayed firm, with DXY at {dxy_level} ({dxy_day}), because rate-based carry trades are coming back as the US still offers the cleanest high-yield major-market exposure.', '<strong>Why it happened:</strong> investors chase interest-rate differentials when they think volatility is manageable, and that flow supports the dollar while pressuring lower-yield currencies and EM funding conditions.', [src['carry_fx']]),
    ],
    'Europe': [
        ('Europe', 'European shares ended at one-week highs because tech strength finally outweighed cyclical caution, but the rally was narrow rather than broad.', '<strong>Why it happened:</strong> investors bought the same semiconductor and platform names that helped the US, while still treating energy-sensitive industrials and exporters more carefully because the macro backdrop remains fragile.', [src['europe_shares']]),
        ('Europe', 'European blue-chip earnings are now set for their strongest growth since late 2022 because a few heavyweight sectors kept margins intact even as the continent’s economy stayed sluggish.', '<strong>Why it happened:</strong> pricing power and cost discipline helped the large caps, but that outperformance is also a sign of concentration, not a sign that Europe suddenly escaped weak demand.', [src['europe_earnings']]),
        ('Europe', 'Europe still looked structurally vulnerable into the close because higher oil and higher US yields is one of the worst combinations for a region with soft growth and imported-energy exposure.', '<strong>Why it happened:</strong> oil works like a tax on Europe while higher yields drain global liquidity. Together they squeeze consumers, raise corporate funding costs, and keep the ECB under pressure.', [src['oil'], src['yield_surge']]),
    ],
    'Asia ex-Japan': [
        ('Asia ex-Japan', 'Asian shares were hit by one-year-high US yields because higher Treasury returns immediately reduce the appeal of regional equities and tighten EM financing conditions.', '<strong>Why it happened:</strong> global investors can earn more in safer US assets when yields jump, so riskier Asian stocks and currencies often take the first hit.', [src['asia_stocks']]),
        ('Asia ex-Japan', 'India’s $1.9 billion credit guarantee stood out because New Delhi decided it was cheaper to protect business cash flow now than wait for the Middle East shock to become a domestic credit problem.', '<strong>Why it happened:</strong> higher fuel and freight costs threaten transport-heavy SMEs first, so the government moved early to stop an energy shock from turning into layoffs and tighter lending.', [src['india_credit'], src['oil']]),
        ('Asia ex-Japan', 'The South Korea-Japan summit announcement mattered regionally because both countries want a tighter political hedge before the next US-China bargaining round and before shipping stress worsens.', '<strong>Why it happened:</strong> shared exposure to trade, chips, and security routes is creating stronger incentives to coordinate rather than improvise separately.', [src['japan_summit'], src['asia_stocks']]),
    ],
    'Middle East & Africa': [
        ('Middle East & Africa', f'Oil stayed elevated, with WTI at {wti_level} ({wti_day}) and Brent at {brent_level} ({brent_day}), because traders still think the Iran confrontation can keep freight, insurance, and inventory premiums high even without a fresh supply outage.', '<strong>Why it happened:</strong> markets are pricing duration risk now, not just spot disruption. That means each geopolitical headline feeds through to shipping and stockpiling behavior.', [src['oil'], src['airlines']]),
        ('Middle East & Africa', 'Iraq seeking IMF and World Bank support is one of the clearest signs that the conflict is becoming a fiscal story, not just an oil-market story.', '<strong>Why it happened:</strong> war-related trade disruption and budget stress can overwhelm fragile public finances quickly, especially when reconstruction needs and subsidy pressures rise together.', [src['iraq'], src['oil']]),
        ('Middle East & Africa', 'Morocco and Kenya both moved to absorb or pass through the shock because governments now have to choose between bigger budget pain and higher consumer fuel pain.', '<strong>Why it happened:</strong> Morocco is using fiscal support to soften the hit, while Kenya raised pump prices because it had less room to hide the cost. Same cause, different balance-sheet capacity.', [src['morocco'], src['kenya']]),
    ],
    'Latin America': [
        ('Latin America', 'Cuba weighing a $100 million US aid offer while distrusting Trump’s motives matters because the island needs relief, but political conditions still shape whether outside money can actually stabilize the economy.', '<strong>Why it happened:</strong> acute shortages create pressure to accept help, but long-running sanctions and mistrust make every aid package look strategic rather than purely humanitarian.', [src['cuba']]),
        ('Latin America', 'Peru’s central bank holding rates at 4.25% matters because policymakers are choosing caution while imported inflation risks remain alive.', '<strong>Why it happened:</strong> when oil, freight, and dollar strength all threaten prices, central banks hesitate to ease even if growth is not especially strong.', [src['peru'], src['oil']]),
        ('Latin America', 'Reuters’ warning that China’s commodity transition needs new models matters for Latin America because the region is still highly levered to Chinese demand, but the composition of that demand is changing fast.', '<strong>Why it happened:</strong> China is buying different mixes of metals, energy, and raw materials as its economy rebalances, so old heuristics can misprice exporters from Brazil to Chile and Peru.', [src['latam_commodities']]),
    ],
}

japan_ja = [
    ('🇯🇵 日本・大引け', f'東京市場は日経平均が{nikkei_level}（{nikkei_day}）で引けた。米金利上昇で世界の金利敏感株に逆風が吹きつつ、USD/JPY {usdjpy_level}（{usdjpy_day}）の円安が輸出株を下支えしたからだ。', '<strong>なぜそうなったか：</strong>米国の強い指標が米長期金利を押し上げ、その金利上昇が世界のリスク資産に逆風となった。一方で日本では円安が外需株の利益期待を支えたため、全面安にはならなかった。', [src['asia_stocks'], src['carry_fx']]),
    ('🇯🇵 日本・物価', '日本の企業物価がエネルギーショックで強く伸びたことは、午後の国内マクロで最重要だった。輸入エネルギー高が工場出荷価格へはっきり波及し、日銀に前倒し行動の根拠を与えたからだ。', '<strong>なぜそうなったか：</strong>中東情勢で燃料と海運コストが上がり、その上昇が電力、ガス、素材コストを通じて企業物価へ速く転嫁された。', [src['japan_wpi'], src['oil']]),
    ('🇯🇵 日本・日銀', 'ロイター調査で日銀が6月に1.0%へ利上げするとの見方が優勢になったのは、今日の物価圧力が一時的ではなく、正常化を急がせる材料と見られたからだ。', '<strong>なぜ市場がそう読むか：</strong>企業物価が強く、円安も残るなら、日銀は待ちすぎるほど信認コストが上がる。だから利上げ観測が午後にさらに固まった。', [src['boj_poll'], src['japan_wpi']]),
    ('🇯🇵 日本・家計', '日銀が食料品や温泉施設などで値上げが続く可能性を指摘したことは政治的にも重い。物価高が生活実感の強い分野に入り始めたからだ。', '<strong>なぜ重要か：</strong>電気、ガス、輸送、農業コストが同時に上がると、これまで我慢していた事業者も価格転嫁せざるを得ない。インフレが「統計」から「家計の不満」に変わる局面だ。', [src['japan_prices'], src['japan_wpi']]),
    ('🇯🇵 日本・外交', '5月19-20日の韓日首脳会談設定は日程以上の意味がある。次の通商・安全保障ストレスの前に、東京とソウルが連携を固めたいからだ。', '<strong>なぜ今か：</strong>米中交渉、エネルギー航路不安、供給網安全保障が同時に重なっている。だから衝撃が来てからではなく、前もって隙間を埋める必要がある。', [src['japan_summit'], src['asia_stocks']]),
    ('🇯🇵 日本・産業政策', '日本の大型半導体投資が引き続き注目されたのは、関税と輸出規制が強まる世界で国内供給力そのものが保険になるからだ。', '<strong>なぜ政府主導になるか：</strong>資金コストが上がり地政学も悪化する局面では、民間任せでは戦略容量が十分に積み上がらない。だから東京は補助金と産業政策へ寄る。', [gnews("Japan's $25 bln chip gambit is worth the wager Reuters when:1d"), src['asia_stocks']]),
]

global_ja = {
    '北米': [
        ('北米', f'米株はS&P500が{spx_level}（{spx_day}）でなお底堅かった。AI関連への買いが続き、北京協議への期待が次の関税悪化懸念を少し和らげたからだ。', '<strong>なぜ上がれたか：</strong>大型テックは景気不安の中でも利益の見通しが比較的強く、投資資金がそこへ集まった。加えて対中対話期待が短期のリスクを少し下げた。', [src['wallstreet']]),
        ('北米', f'米10年債利回りが{us10_level}（{us10_day}）まで高止まりしたことが、本当の圧力源だった。強い景気指標で利下げ期待がさらに後ろへずれたからだ。', '<strong>なぜ重いか：</strong>成長や消費が冷えないほど、債券投資家は長期債を持つ対価として高い利回りを求める。その結果、世界全体の資金条件が引き締まる。', [src['yield_surge']]),
        ('北米', f'ドル指数DXYが{dxy_level}（{dxy_day}）と強かったのは、金利差を取りに行くキャリー取引が戻ってきたからだ。', '<strong>なぜドルが選ばれるか：</strong>主要国の中で米国がなお高利回りを提供し、ボラティリティが管理可能と見られると、資金はドル建てへ流れやすい。', [src['carry_fx']]),
    ],
    '欧州': [
        ('欧州', '欧州株はテック主導で1週間ぶり高値圏へ戻ったが、上昇は広くはなかった。', '<strong>なぜ偏ったか：</strong>米国と同じく半導体やテックが買われた一方、エネルギーや景気に敏感なセクターは慎重に見られた。', [src['europe_shares']]),
        ('欧州', '欧州の大型株決算は2022年後半以来の強い伸びが見込まれているが、それは欧州全体が強いというより、一部大手の耐久力が強いという話だ。', '<strong>なぜそう言えるか：</strong>価格転嫁とコスト管理で大手は耐えているが、域内需要そのものはまだ弱い。', [src['europe_earnings']]),
        ('欧州', 'それでも欧州が構造的に弱い見え方をしたのは、油高と米金利高の組み合わせが最もきつい地域の一つだからだ。', '<strong>なぜ厳しいか：</strong>油高は家計と企業に同時に課税し、米金利高は世界の流動性を吸う。低成長の欧州にはこの二重苦が重い。', [src['oil'], src['yield_surge']]),
    ],
    'アジア（日本除く）': [
        ('アジア（日本除く）', 'アジア株が米金利の1年ぶり高水準で押されたのは、安全資産としての米債の魅力が急に高まったからだ。', '<strong>なぜ売られるか：</strong>米国でより高い利回りが得られるなら、投資家は相対的にリスクの高いアジア株や通貨を減らしやすい。', [src['asia_stocks']]),
        ('アジア（日本除く）', 'インドの19億ドル信用保証は先手対応として目立った。中東ショックを国内の資金繰り悪化へ広げない方が安いと判断したからだ。', '<strong>なぜ先手が必要か：</strong>燃料高と物流高はまず中小企業のキャッシュフローを痛める。そこを止めないと雇用や融資へ波及する。', [src['india_credit'], src['oil']]),
        ('アジア（日本除く）', '韓日首脳会談の設定も地域ニュースとして重い。米中交渉や海運不安が強まる中で、サプライチェーンと安全保障の連携を前倒ししたいからだ。', '<strong>なぜ連携が進むか：</strong>半導体、通商、海上輸送で共通リスクが増え、別々に動くコストが高くなっている。', [src['japan_summit'], src['asia_stocks']]),
    ],
    '中東・アフリカ': [
        ('中東・アフリカ', f'原油はWTI {wti_level}（{wti_day}）、Brent {brent_level}（{brent_day}）と高止まりした。市場がイラン対立を単発の供給停止ではなく、海運・保険・在庫コストの長期化として見ているからだ。', '<strong>なぜ下がりにくいか：</strong>今は現物不足だけでなく、混乱が長引くこと自体に価格がついている。', [src['oil'], src['airlines']]),
        ('中東・アフリカ', 'イラクがIMFと世界銀行の支援を探っているのは、この紛争が原油ニュースではなく財政ニュースにもなったことを示す。', '<strong>なぜそこまで広がるか：</strong>貿易混乱、補助金圧力、歳入不安が重なると、脆弱な財政はすぐに苦しくなる。', [src['iraq'], src['oil']]),
        ('中東・アフリカ', 'モロッコは予算で吸収し、ケニアは燃料価格を引き上げた。同じ衝撃でも、政府のバランスシート余力で対応が分かれた。', '<strong>なぜ対応が違うか：</strong>ショックの原因は同じでも、どこまで補助金で隠せるかは国ごとの財政余力次第だからだ。', [src['morocco'], src['kenya']]),
    ],
    'ラテンアメリカ': [
        ('ラテンアメリカ', 'キューバが米国の1億ドル支援提案を検討しつつ、動機を疑っているのは、支援が必要でも政治条件が常に付いて回るからだ。', '<strong>なぜ単純に受けられないか：</strong>深刻な不足が支援需要を生む一方、制裁と不信が資金を純粋な救済として見えにくくしている。', [src['cuba']]),
        ('ラテンアメリカ', 'ペルー中銀が4.25%で据え置いたのは、輸入インフレ再燃のリスクが残る中で、簡単には緩和へ動けないからだ。', '<strong>なぜ慎重か：</strong>油高、物流高、ドル高が重なると、景気が強くなくても物価リスクは残る。', [src['peru'], src['oil']]),
        ('ラテンアメリカ', '中国のコモディティ需要の変化を古いモデルで読むのは危険だというロイターの指摘は、対中資源依存の大きい中南米には重要だ。', '<strong>なぜ今見直しが必要か：</strong>中国は必要とする資源の組み合わせを変えており、その変化を読み違えるとブラジル、チリ、ペルーの見通しも外しやすい。', [src['latam_commodities']]),
    ],
}

EQ_BODY = '<strong>Why the bigger moves happened:</strong> the notable cross-asset driver was higher US yields. Tech-heavy markets still found buyers because AI earnings are a visible growth pocket, but any move above 2% still needs to be read through the lens of higher duration pressure, energy costs, or both.'
FX_BODY = '<strong>Why it matters:</strong> USD/JPY remains Japan’s fastest stress gauge, while US yields and the dollar are the channels through which North American macro strength is tightening conditions for everyone else.'
CMD_BODY = '<strong>Big mover logic:</strong> if oil is the standout, the cause is still Iran-linked shipping and insurance risk. If gold or crypto swing sharply, the cleaner causal chain is usually a mix of dollar repricing, real-yield moves, and demand for hedges.'

style = """<!DOCTYPE html>
<html lang=\"{lang}\">
<head>
<meta charset=\"utf-8\"/>
<meta content=\"width=device-width, initial-scale=1.0\" name=\"viewport\"/>
<title>CEO Briefing — {title_date}</title>
<link href=\"https://fonts.googleapis.com\" rel=\"preconnect\"/>
<link crossorigin=\"\" href=\"https://fonts.gstatic.com\" rel=\"preconnect\"/>
<link href=\"https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&display=swap\" rel=\"stylesheet\"/>
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
{body}
<script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script>
<script src='audio-player.js'></script>
</body></html>"""


def render_page(ja=False):
    lang = 'ja' if ja else 'en'
    h1 = 'CEO Afternoon Briefing'
    date_line = TODAY_JA + ' 午後版' if ja else TODAY_EN + ' — Afternoon Edition'
    sub = ('🇯🇵 Afternoon delta: Japan shifted from a yen story to a real inflation story as wholesale prices and BOJ hike expectations both firmed · globally, US yields did most of the damage while tech kept masking stress in headline equity indices · Health Score: 58/100' if not ja else '🇯🇵 午後の変化は円相場より物価にあった。企業物価と日銀利上げ観測が同時に強まり、日本はインフレ局面の手触りが増した · 世界では米金利上昇が本当の逆風で、テック高が株指数の見かけを支えた · Health Score: 58/100')
    nav = ('<a href="#japan" class="nav-pill">Japan</a><a href="#global" class="nav-pill">Global</a><a href="#markets" class="nav-pill">Markets</a><a href="#predictions" class="nav-pill">Predictions</a><a href="#bottomline" class="nav-pill">Bottom Line</a>' if not ja else '<a href="#japan" class="nav-pill">日本</a><a href="#global" class="nav-pill">世界</a><a href="#markets" class="nav-pill">市場</a><a href="#predictions" class="nav-pill">予測</a><a href="#bottomline" class="nav-pill">結論</a>')
    jap_cards = '\n'.join(story_card(*item, ja=ja) for item in (japan_ja if ja else japan_en))
    regions = global_ja if ja else global_en
    global_cards = []
    for region, stories in regions.items():
        for tag, headline, body, sources in stories:
            global_cards.append(story_card(tag, headline, body, sources, ja=ja))
    global_cards = '\n'.join(global_cards)
    markets_cards = '\n'.join([
        table_card('EQUITIES' if not ja else '株式', 'End-of-day equity snapshot' if not ja else '主要株価指数の終値', ['Index' if not ja else '指数', 'Level' if not ja else '水準', 'Daily' if not ja else '日次', 'Weekly' if not ja else '週次', 'Monthly' if not ja else '月次', 'YTD'], EQ_ROWS, EQ_BODY if not ja else ' <strong>なぜ大きく動いたか：</strong>今回の横断ドライバーは米金利上昇だ。AI関連の強い市場には買いが残ったが、2%を超えるような動きは金利負担かエネルギーコスト、またはその両方で読むべきだ。', [src['asia_stocks'], src['wallstreet'], src['europe_shares'], src['yahoo']]),
        table_card('FX & RATES' if not ja else '為替・金利', 'Currency and rate pressure points' if not ja else '為替と金利の要点', ['Instrument' if not ja else '項目', 'Level' if not ja else '水準', 'Daily' if not ja else '日次', 'Weekly' if not ja else '週次', 'Monthly' if not ja else '月次', 'YTD'], FX_ROWS, FX_BODY if not ja else ' <strong>なぜ重要か：</strong>USD/JPYは日本の最速ストレス指標であり、米金利とドルは北米の強さが世界全体の資金条件を引き締める経路そのものだ。', [src['carry_fx'], src['yield_surge'], src['yahoo']]),
        table_card('COMMODITIES & CRYPTO' if not ja else '商品・暗号資産', 'Commodity and digital-asset close' if not ja else '商品と暗号資産の終値', ['Asset' if not ja else '資産', 'Price' if not ja else '価格', 'Daily' if not ja else '日次', 'Weekly' if not ja else '週次', 'Monthly' if not ja else '月次', 'YTD'], CMD_ROWS, CMD_BODY if not ja else ' <strong>大きな動きの見方：</strong>原油が目立つなら原因はイラン絡みの海運・保険リスクだ。金や暗号資産が振れるなら、ドル再評価、実質金利、ヘッジ需要の組み合わせで考えるのが分かりやすい。', [src['oil'], src['airlines'], src['yahoo']]),
        f'''        <article class="card fade-in" data-image="{src['yield_surge'].get('image','')}"><span class="card-tag">HEALTH SCORE</span><h3 class="card-headline">{HEALTH}/100, softer than a calm risk-on day because higher US yields and energy stress kept tightening the system even though tech absorbed some of the shock.</h3><p class="card-body"><strong>Why {HEALTH}:</strong> Japan improved on inflation clarity, but the global backdrop worsened because the market had to price a stronger dollar, higher Treasury yields, and still-elevated oil at the same time. That mix usually travels badly.</p><div class="card-sources">\n{source_links([src['yield_surge'], src['oil'], src['japan_wpi'], src['wallstreet']])}\n</div></article>''' if not ja else f'''        <article class="card fade-in" data-image="{src['yield_surge'].get('image','')}"><span class="card-tag">HEALTH SCORE</span><h3 class="card-headline">{HEALTH}/100。穏やかなリスクオン日より低い。テックが一部ショックを吸収しても、米金利高とエネルギー高が同時にシステムを締め付けたからだ。</h3><p class="card-body"><strong>なぜ{HEALTH}か：</strong>日本は物価の見通しが少し明確になったが、世界全体ではドル高、米金利高、油高が同時進行した。この組み合わせは市場に優しくない。</p><div class="card-sources">\n{source_links([src['yield_surge'], src['oil'], src['japan_wpi'], src['wallstreet']])}\n</div></article>'''
    ])
    pred_cards = (
        story_card('TOMORROW', 'Tomorrow’s first question is whether Japan’s inflation surprise turns into a still-more-explicit BOJ signal, because today’s data raised the cost of patience.', '<strong>Why to watch it:</strong> if officials validate the stronger hike path, yen expectations can change fast and reprice exporters, rates, and domestic financials together.', [src['japan_wpi'], src['boj_poll']], ja=False) + '\n' +
        story_card('WEEK AHEAD', 'The broader risk is that higher US yields and high oil stop offsetting each other in markets and start compounding each other in the real economy.', '<strong>Why to watch it:</strong> that is the point where what looked like a tech-led equity resilience story becomes an earnings-downgrade and demand-slowdown story instead.', [src['yield_surge'], src['oil'], src['airlines']], ja=False)
    ) if not ja else (
        story_card('明日', '明日の第一論点は、日本の物価上振れがさらに明確な日銀シグナルへつながるかどうかだ。今日の数字で「待つコスト」は上がった。', '<strong>なぜ重要か：</strong>当局が利上げパスを追認すれば、円、輸出株、金利、金融株がまとめて再価格付けされやすい。', [src['japan_wpi'], src['boj_poll']], ja=True) + '\n' +
        story_card('週間見通し', 'より大きなリスクは、米金利高と油高が市場で相殺されるのではなく、実体経済で相乗的に効き始めることだ。', '<strong>なぜ重要か：</strong>その局面に入ると、テック主導で指数が強く見える話から、利益下方修正と需要減速の話へ移りやすい。', [src['yield_surge'], src['oil'], src['airlines']], ja=True)
    )
    bottom = ('<p>The real afternoon change was that <strong>Japan stopped looking like a pure FX story and started looking like an inflation-and-BOJ story, while the rest of the world kept getting squeezed by higher US yields and expensive energy.</strong> <strong>Bottom line:</strong> Japan gained policy clarity, but the global system got tighter.</p>' if not ja else '<p><strong>午後の本当の変化は、日本が単なる為替の話から、物価と日銀の話へ移ったことだ。</strong>一方で世界は米金利高とエネルギー高でさらに締まった。<strong>結論：</strong>日本は政策の輪郭が少し見えたが、世界の資金環境は悪化した。</p>')
    body = f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html"{' class="active"' if not ja else ''}>EN</a><span class="sep">/</span><a href="ja.html"{' class="active"' if ja else ''}>JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><h1>{h1}</h1><div class="edition-date">{date_line}</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills">{nav}</nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">{'日本アップデート' if ja else 'Japan Update — In Depth'}</h2></div><div class="cards">{jap_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">{'世界の動き' if ja else 'Global — By Continent'}</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">{'市場と経済' if ja else 'Markets & Economy'}</h2></div><div class="cards">{markets_cards}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">{'予測' if ja else 'Predictions'}</h2></div><div class="cards">{pred_cards}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 {'結論' if ja else 'Bottom Line'}</h3>{bottom}</div></section></main><footer class='footer'><p>CEO Afternoon Briefing · Generated by Sanbot · {TODAY_JA if ja else TODAY_EN}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters via Google News RSS, Yahoo Finance</p></footer>'''
    return style.format(lang=lang, title_date=TITLE_DATE, body=body)


(BASE / 'index.html').write_text(render_page(False))
(BASE / 'ja.html').write_text(render_page(True))
print('updated index.html and ja.html')
