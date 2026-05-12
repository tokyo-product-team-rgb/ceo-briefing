# -*- coding: utf-8 -*-
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BASE = Path('/Users/xand/.openclaw/workspace/ceo-briefing')
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TODAY_EN = 'Tuesday, May 12, 2026'
TODAY_JA = '2026年5月12日（火）'
TITLE_DATE = 'May 12, 2026'
WAR_DAY = '73'
HEALTH = 66


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
    'hormuz': gnews('NATO Rutte Trump wants Hormuz pledges within days Reuters'),
    'japan_yen_us': gnews('Japan keeps US close as it signals unlimited yen defence Reuters'),
    'japan_intervention': gnews('Japan may have spent $32 billion in additional yen-buying intervention Reuters'),
    'japan_election_market': gnews("Instant View Japan's markets react to Takaichi's historic election victory Reuters"),
    'japan_takaichi_tax': gnews('Landslide election win clears path for Japan Takaichi to deliver tax cuts Reuters'),
    'japan_china': gnews("Japan PM's big election win could mean more beef with Beijing Reuters"),
    'japan_trade_template': gnews('Breakingviews Japan trade deal breaks US tariff template Reuters'),
    'softbank_line': gnews('SoftBank in talks with Naver over control of Line operator LY Reuters'),
    'us_jobs': gnews('Stocks rally dollar higher in wake of US jobs numbers Reuters'),
    'us_earnings': gnews("Wall Street's earnings fantasies may soon get harsh reality check Reuters"),
    'us_energy_tariffs': gnews('Trump tariff reversal could cut costs for US energy firms but will likely leave broader flows unchanged Reuters'),
    'eu_tariffs': gnews('US to move forward with plans to hike EU car tariffs Reuters'),
    'eu_shares': gnews('European shares pull back as fragile US-Iran truce weighs on sentiment Reuters'),
    'eu_middleeast': gnews('European shares drop as Middle East continues to hit sentiment Reuters'),
    'china_rebound': gnews('China is coming back and the timing couldnt be better Reuters'),
    'china_q1': gnews("China's Q1 economic rebound faces rough seas as Iran war jolts global outlook Reuters"),
    'jimmy_lai': gnews('China critic Jimmy Lai sentenced to 20 years in jail after landmark Hong Kong trial Reuters'),
    'india_credit': gnews('India approves $1.9 billion credit guarantee to support businesses hit by Middle East crisis Reuters'),
    'india_rupee': gnews('Rupee gains on week US-Iran jitters spark choppy trading Reuters'),
    'airlines': gnews('Airlines cancel flights in response to Middle East conflict Reuters'),
    'jetfuel': gnews("Iran war jet fuel concerns cloud airlines' summer holiday plans Reuters"),
    'brazil_trump': gnews("Brazil's Lula reports progress in relations with US after talks with Trump Reuters"),
    'brazil_satisfied': gnews("Brazil's Lula says he's very satisfied after meeting with Trump Reuters"),
    'vanuatu': gnews('Australia Vanuatu security agreement delayed Reuters'),
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

japan = [
    {
        'tag': '🇯🇵 JAPAN · FX DEFENCE',
        'headline': f'Japan spent the afternoon tightening coordination with Washington because defending the yen near USD/JPY {usdjpy_level} ({usdjpy_day}) works better if speculators think Tokyo has US political cover, not just verbal resolve.',
        'body': '<strong>Why it happened:</strong> Tokyo knows unilateral jawboning fades quickly when the interest-rate gap still favors the dollar. Keeping the US close raises the perceived cost of leaning against Japan, so the policy chain is diplomatic alignment first, then stronger currency signalling second.',
        'sources': [src['japan_yen_us'], src['hormuz']],
    },
    {
        'tag': '🇯🇵 JAPAN · INTERVENTION',
        'headline': 'Suspected multi-day yen-buying intervention became the afternoon’s clearest new signal because officials appear to have concluded that imported inflation risk was rising faster than market discipline alone could contain it.',
        'body': '<strong>Why it happened:</strong> once a weak yen starts feeding directly into food, fuel, and political credibility, waiting gets more expensive. That is why the likely $32 billion deployment matters, it suggests the Ministry of Finance judged passivity as the riskier option.',
        'sources': [src['japan_intervention'], src['japan_yen_us']],
    },
    {
        'tag': '🇯🇵 JAPAN · MARKET CLOSE',
        'headline': f'Nikkei finished at {nikkei_level} ({nikkei_day}) because Takaichi’s victory gave investors a fresh domestic-growth story even while currency stress kept exporters and policy-sensitive names under a microscope.',
        'body': '<strong>Why it happened:</strong> markets liked the prospect of tax cuts and more predictable stimulus discipline, which supports domestic demand. But the same session stayed selective because a stronger intervention stance and geopolitical risk complicate the earnings outlook for globally exposed companies.',
        'sources': [src['japan_election_market'], src['japan_takaichi_tax']],
    },
    {
        'tag': '🇯🇵 JAPAN · POLITICS / CHINA',
        'headline': 'Takaichi’s landslide immediately raised the geopolitical temperature because a stronger mandate makes it easier for her to take a firmer line on China without fearing an instant domestic backlash.',
        'body': '<strong>Why it happened:</strong> electoral strength widens room for security and trade positioning. Beijing now has more reason to test rhetoric, while Tokyo has more incentive to prove resolve, so the causal chain runs from domestic mandate to external friction.',
        'sources': [src['japan_china'], src['japan_takaichi_tax']],
    },
    {
        'tag': '🇯🇵 JAPAN · TRADE / US',
        'headline': 'Japan’s trade template mattered more in the afternoon because Tokyo is trying to show Washington that cooperation on security and supply chains should buy tariff flexibility.',
        'body': '<strong>Why it happened:</strong> Japan cannot fully offset US tariff risk with rhetoric, so it is packaging itself as the strategic ally that solves problems America cares about, from semiconductors to regional security. The goal is to change the cost-benefit math in Washington.',
        'sources': [src['japan_trade_template'], src['japan_yen_us']],
    },
    {
        'tag': '🇯🇵 JAPAN · CORPORATE',
        'headline': 'SoftBank’s talks over tighter control of Line operator LY stood out because Japanese corporate strategy is shifting toward assets that secure distribution, data, and domestic digital leverage while the external backdrop gets noisier.',
        'body': '<strong>Why it happened:</strong> when geopolitics makes macro demand less predictable, boards put more value on platforms they can control directly. The deal logic is therefore defensive and strategic at the same time, own the customer pipe before cross-border volatility gets worse.',
        'sources': [src['softbank_line'], src['japan_trade_template']],
    },
]

global_regions = {
    'North America': [
        ('North America', f'US stocks rallied into the close, with the S&P 500 at {spx_level} ({spx_day}), because payroll resilience reassured investors that growth has not cracked yet even as oil and tariff risks stayed in the background.', '<strong>Why it happened:</strong> stronger jobs data lowers immediate recession fear, so traders were willing to buy cyclical risk. The move was not cleanly bullish, though, because the same strength also delays hopes for fast Fed easing.', [src['us_jobs'], src['us_earnings']]),
        ('North America', 'Wall Street’s earnings optimism started looking vulnerable because analysts have been slow to fully price how higher energy, tariffs, and freight costs can squeeze margins all at once.', '<strong>Why it happened:</strong> when multiple cost pressures hit together, companies lose the easy option of blaming one temporary factor. Investors are now questioning whether consensus estimates still assume a world that no longer exists.', [src['us_earnings'], src['us_energy_tariffs']]),
        ('North America', 'Trump’s tariff adjustment for energy inputs mattered because Washington is trying to protect domestic producers from cost spikes without abandoning the broader protectionist message.', '<strong>Why it happened:</strong> the administration needs to avoid hurting politically useful industries with its own trade policy. That creates selective carve-outs, which are effectively an admission that blanket tariffs were starting to feed back into US operating costs.', [src['us_energy_tariffs']]),
    ],
    'Europe': [
        ('Europe', 'Europe had a harder afternoon because the US move toward higher EU car tariffs hit one of the region’s most exposed industrial nerves.', '<strong>Why it happened:</strong> autos sit at the intersection of exports, manufacturing employment, and political symbolism. When tariff risk rises there, investors read it as a direct threat to both earnings and already-fragile European growth.', [src['eu_tariffs']]),
        ('Europe', 'European shares pulled back because the market stopped treating the US-Iran truce language as stabilizing and started treating it as too fragile to change positioning.', '<strong>Why it happened:</strong> a ceasefire only helps risk assets if traders believe it lowers the probability of renewed supply disruption. Europe sold off because that credibility was not there.', [src['eu_shares'], src['eu_middleeast']]),
        ('Europe', 'The region stayed heavy because Middle East headlines raise energy costs for an economy that still has weak domestic momentum and little room for another imported inflation shock.', '<strong>Why it happened:</strong> Europe is more vulnerable when oil jumps into soft growth. Higher energy becomes a tax on households, a margin hit for industry, and a policy headache for the ECB at the same time.', [src['eu_middleeast'], src['eu_shares']]),
    ],
    'Asia ex-Japan': [
        ('Asia ex-Japan', 'China’s rebound story gained traction because investors now see Beijing as one of the few large economies that could stabilize global demand if the West gets dragged down by energy and trade shocks.', '<strong>Why it happened:</strong> when the US and Europe look more policy-constrained, any sign of Chinese recovery becomes more valuable to global markets. Timing matters because China is being judged relative to weakening peers, not against perfection.', [src['china_rebound'], src['china_q1']]),
        ('Asia ex-Japan', 'But China’s Q1 rebound also looked more fragile because the Iran war threatens shipping, commodity costs, and external demand before the recovery has fully broadened.', '<strong>Why it happened:</strong> export-sensitive recoveries depend on stable trade lanes and predictable input costs. The Middle East shock attacks both, which is why the market is upgrading downside scenarios again.', [src['china_q1'], src['hormuz']]),
        ('Asia ex-Japan', 'India’s emergency credit guarantee mattered because New Delhi judged the Middle East shock as serious enough to warrant cushioning businesses before stress spread from fuel costs into jobs and financing.', '<strong>Why it happened:</strong> India imports energy, so oil pain can quickly hit working capital, transport, and inflation expectations. The package is meant to interrupt that transmission chain before it becomes a broader slowdown.', [src['india_credit'], src['india_rupee']]),
    ],
    'Middle East & Africa': [
        ('Middle East & Africa', f'WTI crude held near {wti_level} ({wti_day}) because markets are still pricing Hormuz and regional shipping risk as a persistent supply threat rather than a one-day scare.', '<strong>Why it happened:</strong> oil stays elevated when traders believe the risk window is measured in weeks, not hours. Insurance, rerouting, and inventory hedging all support prices even without an outright physical outage.', [src['hormuz'], src['airlines']]),
        ('Middle East & Africa', 'Airlines kept cancelling flights because the conflict is disrupting the economics of aviation through route uncertainty, fuel costs, and insurance assumptions at the same time.', '<strong>Why it happened:</strong> carriers can absorb one stressor, but not three synchronized ones. Once safe routing, jet fuel pricing, and schedule reliability all weaken together, cancellations become the rational response.', [src['airlines'], src['jetfuel']]),
        ('Middle East & Africa', 'The broader region remained the market’s top macro variable because every new headline now feeds straight into inflation expectations, central-bank timing, and consumer confidence far outside the region itself.', '<strong>Why it happened:</strong> Middle East risk matters globally when it changes the price of transport and energy, not only because of battlefield developments. That is why even faraway equity markets are trading the story so directly.', [src['hormuz'], src['jetfuel']]),
    ],
    'Latin America': [
        ('Latin America', 'Lula’s progress report after meeting Trump mattered because Brazil is trying to keep US trade relations functional before tariffs or geopolitical alignment demands get tougher.', '<strong>Why it happened:</strong> Brazil benefits from strategic ambiguity, but that becomes harder when Washington is using trade and diplomacy more coercively. Lula is signaling pragmatism to preserve room to maneuver.', [src['brazil_trump'], src['brazil_satisfied']]),
        ('Latin America', 'The upbeat tone from Lula also mattered domestically because he needs to show Brazilian business that diplomacy can still reduce external shocks before they hit exports and investment plans.', '<strong>Why it happened:</strong> positive optics lower uncertainty for exporters and agribusiness. The political logic is simple, foreign stability is a domestic economic message.', [src['brazil_satisfied'], src['brazil_trump']]),
        ('Latin America', 'Latin America stayed leveraged to the same global theme, whichever countries can keep access to both Washington and commodity demand will outperform if the tariff-and-oil regime lasts.', '<strong>Why it happened:</strong> the region wins or loses on trade channels and price cycles. Today’s diplomacy matters because it shapes those channels before the next shock arrives.', [src['brazil_trump']]),
    ],
    'Oceania': [
        ('Oceania', 'The delayed Australia-Vanuatu security agreement mattered because Pacific states are still resisting the idea that strategic urgency should override their bargaining leverage.', '<strong>Why it happened:</strong> smaller countries know great-power competition increases their value. Delay is therefore not drift, it is negotiation power being exercised.', [src['vanuatu']]),
        ('Oceania', 'Oceania also stayed tied to the wider risk picture because any prolonged energy and shipping disruption raises import costs for island economies with limited buffers.', '<strong>Why it happened:</strong> distance makes freight shocks bite harder. That is why Pacific political bargaining now sits inside a much larger logistics and security story.', [src['vanuatu'], src['hormuz']]),
        ('Oceania', 'Australia’s regional security timing became more sensitive because allies want faster alignment while local partners want proof that alignment will bring concrete benefits, not just pressure.', '<strong>Why it happened:</strong> security deals move when incentives are clear. The delay shows the benefits case has not yet fully outrun sovereignty concerns.', [src['vanuatu']]),
    ],
}

japan_ja = [
    ('🇯🇵 日本・円防衛', f'日本が午後にワシントンとの連携を強めたのは、USD/JPY {usdjpy_level}（{usdjpy_day}）近辺で円を守るには、口先だけでなく「米国が背後にいる」と投機筋に思わせる必要があるからだ。', '<strong>なぜそう動いたか：</strong>金利差がなおドル優位である以上、日本単独のけん制は効力が続きにくい。だから先に外交の後ろ盾を固め、次に為替シグナルを強めるという順番になっている。', [src['japan_yen_us'], src['hormuz']]),
    ('🇯🇵 日本・介入', '追加の円買い介入観測が午後の最大の新材料になった。政府は、輸入インフレの政治コストが市場任せで放置できる水準を超えたと判断した可能性が高い。', '<strong>なぜ介入観測が重いか：</strong>円安が燃料や食品価格に直結し始めると、何もしないこと自体が高コストになる。約320億ドル規模とみられる対応は、「待つほうが危険」という判断を示す。', [src['japan_intervention'], src['japan_yen_us']]),
    ('🇯🇵 日本・大引け', f'日経平均は{nikkei_level}（{nikkei_day}）で引けた。高市勝利で内需と減税期待が強まった一方、為替防衛と地政学が銘柄選別を厳しくしたからだ。', '<strong>なぜこの引け味か：</strong>市場は税制や財政運営の見通し改善を好感したが、介入強化や外部リスクはグローバル企業の業績見通しを複雑にする。つまり好材料はあるが、全面的に強気にはなりにくい。', [src['japan_election_market'], src['japan_takaichi_tax']]),
    ('🇯🇵 日本・政治/中国', '高市氏の大勝は対中温度を上げやすい。強い民意を得た首相は、国内反発を恐れずにより強い安全保障姿勢を取りやすくなるからだ。', '<strong>なぜ外に波及するか：</strong>国内の勝利は外交の裁量を広げる。北京は試しに来やすくなり、東京は強さを示したくなるので、選挙結果が対外摩擦に直結する。', [src['japan_china'], src['japan_takaichi_tax']]),
    ('🇯🇵 日本・通商/米国', '日本の通商テンプレートが午後に重みを増したのは、安全保障や供給網で米国に協力することが、関税柔軟化の交渉材料になると東京が見ているからだ。', '<strong>なぜこの組み立てか：</strong>言葉だけでは関税は動かない。だから日本は半導体や地域安全保障で「米国の課題を解く同盟国」という位置づけを強め、ワシントンの損得勘定を変えようとしている。', [src['japan_trade_template'], src['japan_yen_us']]),
    ('🇯🇵 日本・企業', 'SoftBankによるLINE運営会社LYの支配強化交渉が目立ったのは、外部環境が騒がしいほど、顧客接点とデータ基盤を自前で握る価値が上がるからだ。', '<strong>なぜ今この手か：</strong>地政学で需要が読みにくくなるほど、企業は自分で制御できる配信面とプラットフォームに価値を置く。守りと攻めを兼ねた再編だ。', [src['softbank_line'], src['japan_trade_template']]),
]

global_regions_ja = {
    '北米': [
        ('北米', f'米株は、S&P 500が{spx_level}（{spx_day}）まで戻した。雇用の底堅さが景気失速懸念を和らげた一方、油高と関税はなお後景に残ったからだ。', '<strong>なぜ上がれたか：</strong>雇用が強ければ景気後退の即時リスクは下がるため、投資家は景気敏感株を買いやすい。ただし同じ強さは利下げ期待を後ろ倒しにもするので、上昇の質はまだ脆い。', [src['us_jobs'], src['us_earnings']]),
        ('北米', '米企業の利益見通しが危うく見え始めたのは、エネルギー、関税、物流のコスト圧力を市場がまだ十分に織り込んでいないからだ。', '<strong>なぜ今疑われるか：</strong>複数コストが同時に上がると、一時要因として処理しにくい。コンセンサス予想が、もう存在しない前提に立っているのではないかという疑いが強まっている。', [src['us_earnings'], src['us_energy_tariffs']]),
        ('北米', 'エネルギー関連の関税調整が重要なのは、米政権が保護主義を維持しながらも、自国産業への副作用は和らげたいと考えているからだ。', '<strong>なぜ選別的になるか：</strong>一律関税は、守りたい産業にもコスト上昇として跳ね返る。部分的な見直しは、その自己矛盾が表面化した結果だ。', [src['us_energy_tariffs']]),
    ],
    '欧州': [
        ('欧州', '欧州は午後に苦しかった。米国のEU車関税引き上げ方針が、地域の最も弱い産業神経のひとつを直撃したからだ。', '<strong>なぜ自動車が痛いか：</strong>自動車は輸出、雇用、政治の交点にある。そこへの関税圧力は、企業利益だけでなく欧州成長全体への不安に直結する。', [src['eu_tariffs']]),
        ('欧州', '欧州株が戻りきれないのは、米イラン停戦ムードが相場を落ち着かせるほど信頼されていないからだ。', '<strong>なぜ効かないか：</strong>停戦が本当に供給不安を減らすと信じられなければ、投資家はリスクを戻さない。今回売られたのは、その信認不足の表れ。', [src['eu_shares'], src['eu_middleeast']]),
        ('欧州', '中東発のエネルギー不安が特に重いのは、内需が弱い欧州にとって油高が家計、企業、ECBを同時に苦しめるからだ。', '<strong>なぜ三重苦か：</strong>エネルギー高は家計には実質増税、企業には利益圧迫、政策当局にはインフレ再燃リスクとなる。だから欧州は反応が重い。', [src['eu_middleeast'], src['eu_shares']]),
    ],
    'アジア（日本除く）': [
        ('アジア（日本除く）', '中国回復論が強まったのは、西側主要国がエネルギーと通商ショックで制約を抱える中、需要の下支え役として中国の相対価値が上がったからだ。', '<strong>なぜタイミングが重要か：</strong>米欧が動きにくい局面では、中国の改善サインは平時以上に大きく見える。完璧だからではなく、他が弱くなっているから価値が増す。', [src['china_rebound'], src['china_q1']]),
        ('アジア（日本除く）', 'ただし中国のQ1反発は、中東戦争が物流と原材料コストを揺らすほど脆さも意識された。', '<strong>なぜ足元が危ういか：</strong>輸出主導の回復は、安定した航路と予見可能な投入コストが前提だ。今回のショックはその両方を傷つける。', [src['china_q1'], src['hormuz']]),
        ('アジア（日本除く）', 'インドの緊急信用保証は、油高ショックが資金繰り、雇用、インフレへ波及する前に企業を支える必要があると政府が見たからだ。', '<strong>なぜ先回りか：</strong>インドはエネルギー輸入国なので、燃料高は運転資金を通じて景気全体へ広がりやすい。政策はその伝播を途中で切る狙い。', [src['india_credit'], src['india_rupee']]),
    ],
    '中東・アフリカ': [
        ('中東・アフリカ', f'WTIが{wti_level}（{wti_day}）近辺で高止まりしたのは、ホルムズ海峡と周辺物流のリスクが一過性ではなく、数週間単位の供給不安として値付けされているからだ。', '<strong>なぜ高止まりか：</strong>市場は現物不足だけでなく、保険料、迂回輸送、在庫積み増しも織り込む。だから物理的な停止がなくても価格は支えられる。', [src['hormuz'], src['airlines']]),
        ('中東・アフリカ', '航空会社の欠航が続くのは、航路不確実性、燃料費、保険前提の3つが同時に悪化しているからだ。', '<strong>なぜ長引くか：</strong>1つなら吸収できても、3つ重なると通常の運航採算が崩れる。欠航は過剰反応ではなく合理的対応だ。', [src['airlines'], src['jetfuel']]),
        ('中東・アフリカ', 'この地域が世界相場の主変数であり続けるのは、どの見出しもすぐにインフレ期待、中銀の時間軸、消費者心理に波及するからだ。', '<strong>なぜ遠くても効くか：</strong>戦況そのものより、輸送とエネルギー価格を通じた波及が世界経済を動かしている。だから遠い市場も直接反応する。', [src['hormuz'], src['jetfuel']]),
    ],
    'ラテンアメリカ': [
        ('ラテンアメリカ', 'ルラ大統領がトランプ会談後の進展を強調したのは、関税や同盟圧力が強まる前に米国との実務関係を保っておきたいからだ。', '<strong>なぜ実利重視か：</strong>ブラジルは曖昧さを価値に変えてきたが、米国が通商と外交をより強く結びつけるほど、その余地は狭まる。だから今は実務的安定が優先。', [src['brazil_trump'], src['brazil_satisfied']]),
        ('ラテンアメリカ', 'ルラの前向きなトーンは国内向けにも重要だ。輸出企業や投資家に、外部ショックを外交で和らげられると示したいからだ。', '<strong>なぜ国内経済メッセージになるか：</strong>対外安定は、そのまま投資判断と輸出計画の安心材料になる。外交の演出が景気対策でもある。', [src['brazil_satisfied'], src['brazil_trump']]),
        ('ラテンアメリカ', 'ラテンアメリカ全体では、ワシントンとの接点と資源需要の両方を維持できる国ほど、この油高・関税局面で優位に立ちやすい。', '<strong>なぜそこが分岐点か：</strong>この地域の勝敗は、通商チャネルと価格サイクルで決まりやすい。今日の外交は次のショック前のポジション取りだ。', [src['brazil_trump']]),
    ],
    'オセアニア': [
        ('オセアニア', '豪州とバヌアツの安保協定遅延が示したのは、太平洋の島しょ国が戦略的緊急性より交渉力を優先できるほど、自らの価値を理解していることだ。', '<strong>なぜ遅延が力になるか：</strong>大国間競争が激しいほど、小国の価値は上がる。遅らせること自体が交渉カードになる。', [src['vanuatu']]),
        ('オセアニア', 'オセアニアも広域リスクと無縁ではない。エネルギーと海運の混乱が長引くほど、輸入依存の島しょ経済ほどコスト圧迫を受けやすいからだ。', '<strong>なぜ波及が大きいか：</strong>距離が長い地域ほど運賃ショックが効く。地域政治も物流と安全保障の大きな文脈に包まれている。', [src['vanuatu'], src['hormuz']]),
        ('オセアニア', '豪州の地域安全保障の進め方が難しいのは、同盟国は急ぎたくても、相手国は主権に見合う見返りを求めるからだ。', '<strong>なぜ足踏みするか：</strong>安全保障協定は、圧力だけでは進まない。利益の見え方が主権不安を上回る必要がある。', [src['vanuatu']]),
    ],
}

market_sources = [src['hormuz'], src['us_jobs'], src['eu_tariffs'], src['china_rebound'], src['yahoo']]


def build_body(lang='en'):
    if lang == 'en':
        japan_cards = '\n'.join(story_card(x['tag'], x['headline'], x['body'], x['sources']) for x in japan)
        global_cards = []
        for _, items in global_regions.items():
            for tag, headline, body, sources in items:
                global_cards.append(story_card(tag, headline, body, sources))
        global_cards = '\n'.join(global_cards)
        markets = '\n'.join([
            table_card('EQUITIES', 'End-of-day equity snapshot', ['Index', 'Level', 'Daily', 'Weekly', 'Monthly', 'YTD'], EQ_ROWS, '<strong>Why the larger moves happened:</strong> Japan’s close was helped by election clarity and tax-cut hopes, US equities by strong jobs, and Europe less so because tariff and energy risk hit a weaker growth base. Any move above 2% should be read through either policy repricing or conflict-driven input-cost stress, not in isolation.', market_sources),
            table_card('FX & RATES', 'Currency and rate pressure points', ['Instrument', 'Level', 'Daily', 'Weekly', 'Monthly', 'YTD'], FX_ROWS, '<strong>Why it matters:</strong> USD/JPY is still the fastest read on how much pain Tokyo is willing to absorb before escalating defence. Treasury yields and the dollar stayed sensitive to jobs data because resilient growth reduces recession fear while also delaying the timing of easier policy.', market_sources),
            table_card('COMMODITIES & CRYPTO', 'Commodity and digital-asset close', ['Asset', 'Price', 'Daily', 'Weekly', 'Monthly', 'YTD'], CMD_ROWS, '<strong>Big mover logic:</strong> if crude is up more than 2%, the best explanation is still shipping-duration risk around Hormuz and the knock-on effect on aviation and inventories. If crypto or silver move more than 2%, the cleaner read is dollar repricing and changing inflation-hedge demand.', market_sources),
            f'''        <article class="card fade-in" data-image="{market_sources[0].get('image','')}"><span class="card-tag">HEALTH SCORE</span><h3 class="card-headline">{HEALTH}/100, firmer than the morning because Japan gained political clarity and the US got a jobs cushion, but still vulnerable to any renewed oil-shipping shock.</h3><p class="card-body"><strong>Why {HEALTH}:</strong> the afternoon improved because Takaichi’s mandate gave Tokyo a clearer policy story and US payrolls reduced immediate recession fear. The score stays below comfort because the same tape still depends heavily on whether Hormuz, tariffs, and airline disruption worsen from here.</p><div class="card-sources">\n{source_links(market_sources)}\n          </div></article>'''
        ])
        predictions = '''        <article class="card fade-in collapsible" data-image=""><span class="card-tag">TOMORROW</span><h3 class="card-headline">Watch whether Japan follows diplomatic yen signalling with a cleaner intervention or policy message, because markets now know officials are willing to spend real money.</h3><div class="tap-hint">Tap to expand</div><p class="card-body"><strong>Why it matters:</strong> once intervention is believable, the next question is endurance. If the yen slips again quickly, traders will test how much political capital Tokyo is ready to burn.</p><div class="card-sources">\n''' + source_links([src['japan_intervention'], src['japan_yen_us']]) + '''\n          </div></article>
        <article class="card fade-in collapsible" data-image=""><span class="card-tag">WEEK AHEAD</span><h3 class="card-headline">The bigger test is whether Middle East shipping risk stays a markets story or starts becoming an earnings, inflation, and travel-capacity story everywhere else.</h3><div class="tap-hint">Tap to expand</div><p class="card-body"><strong>Why it matters:</strong> once oil, freight, insurance, and route disruption hit company guidance together, volatility usually stops being headline-driven and becomes structural.</p><div class="card-sources">\n''' + source_links([src['hormuz'], src['airlines'], src['jetfuel']]) + '''\n          </div></article>'''
        bottom_line = 'The real afternoon change was that <strong>Japan gained a clearer political and policy edge just as the rest of the world kept getting dragged back into oil-and-tariff math.</strong> Takaichi’s mandate, probable intervention, and a tighter US alignment gave Tokyo more visible tools than it had in the morning. <strong>Bottom line:</strong> Japan improved on relative terms, but the world is still being priced by Hormuz risk, transport disruption, and margin compression.'
        sub = f'🇯🇵 Afternoon Tokyo turned on three new things: a stronger Takaichi mandate, more credible yen defence, and fresh trade leverage with Washington, which helped offset the old oil-and-import-cost squeeze · SoftBank’s LY talks showed corporates still hunting controllable domestic advantages · Globally, jobs held up in the US, Europe stayed trapped between tariffs and energy, and Hormuz kept dictating the macro tape · Health Score: {HEALTH}/100'
        footer = 'CEO Afternoon Briefing · Generated by Sanbot · Tuesday, May 12, 2026'
        return f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html" class="active">EN</a><span class="sep">/</span><a href="ja.html">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">{WAR_DAY}</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_EN} — Afternoon Edition</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">Japan</a><a href="#global" class="nav-pill">Global</a><a href="#markets" class="nav-pill">Markets</a><a href="#predictions" class="nav-pill">Predictions</a><a href="#bottomline" class="nav-pill">Bottom Line</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">Japan Update — In Depth</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">Global — By Continent</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">Markets & Economy</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">Predictions</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''

    japan_cards = '\n'.join(story_card(t, h, b, s, ja=True) for t, h, b, s in japan_ja)
    global_cards = []
    for _, items in global_regions_ja.items():
        for tag, headline, body, sources in items:
            global_cards.append(story_card(tag, headline, body, sources, ja=True))
    global_cards = '\n'.join(global_cards)
    markets = '\n'.join([
        table_card('株式', '引け後マーケット一覧', ['指数', '水準', '日次', '週次', '月次', '年初来'], EQ_ROWS, '大きな値動きの主因は、日本では選挙結果と減税期待、米国では雇用の底堅さ、欧州では関税とエネルギー不安だった。2%超の変動は、政策見通しの変化か、紛争起点のコストショックで読むのが自然。', market_sources),
        table_card('為替・金利', '通貨と金利の要点', ['指標', '水準', '日次', '週次', '月次', '年初来'], FX_ROWS, 'USD/JPYは、日本がどこまで痛みに耐え、いつ防衛を強めるかを映す最速指標。米金利とドルは、強い雇用が景気不安を和らげる一方で、利下げ時期を遅らせるという二面性で動いた。', market_sources),
        table_card('商品・暗号資産', '商品とデジタル資産の引け', ['資産', '価格', '日次', '週次', '月次', '年初来'], CMD_ROWS, '原油が2%超動くなら、今はホルムズ海峡周辺の輸送期間リスクと、航空・在庫への波及で説明するのが最も自然。暗号資産や銀の大きな動きは、ドル再評価とインフレヘッジ需要の変化で読むべき。', market_sources),
        f'''        <article class="card fade-in" data-image="{market_sources[0].get('image','')}"><span class="card-tag">ヘルススコア</span><h3 class="card-headline">{HEALTH}/100、朝よりは改善。ただし改善の理由は安心ではなく、日本の政策視界と米雇用の下支えが見えたからだ。</h3><p class="card-body"><strong>なぜ{HEALTH}か：</strong>高市政権の明確な mandate と米雇用の強さで、朝より政策と景気の手掛かりが増えた。一方でホルムズ、関税、航空混乱が悪化すればすぐに崩れるため、快適圏には届かない。</p><div class="card-sources">\n{source_links(market_sources)}\n          </div></article>'''
    ])
    predictions = '''        <article class="card fade-in collapsible" data-image=""><span class="card-tag">明日</span><h3 class="card-headline">日本が外交的な円防衛シグナルを、より明確な介入や政策メッセージに強めるかを注視。</h3><div class="tap-hint">タップして展開</div><p class="card-body"><strong>なぜ重要か：</strong>介入の存在が信じられた今、市場の次の関心は持久力に移る。円がすぐに崩れれば、当局の覚悟が再び試される。</p><div class="card-sources">\n''' + source_links([src['japan_intervention'], src['japan_yen_us']]) + '''\n          </div></article>
    <article class="card fade-in collapsible" data-image=""><span class="card-tag">今週</span><h3 class="card-headline">中東の海運リスクが相場の話で終わるのか、利益、物価、旅行供給へ本格的に波及するのかが次の分岐点。</h3><div class="tap-hint">タップして展開</div><p class="card-body"><strong>なぜそこか：</strong>原油、運賃、保険、運航混乱が同時に企業ガイダンスへ入ると、ボラティリティは見出し主導から構造要因へ変わる。</p><div class="card-sources">\n''' + source_links([src['hormuz'], src['airlines'], src['jetfuel']]) + '''\n          </div></article>'''
    bottom_line = '午後に変わった本質は、<strong>世界がなお油高と関税の算数で動く中、日本だけは政治と政策の手数が朝より増えた</strong>ことだ。高市氏の mandate、介入観測、対米レバレッジが東京の相対優位を押し上げた。<strong>結論：</strong>日本は相対改善したが、世界全体は依然としてホルムズ、輸送混乱、利益圧迫で値付けされている。'
    sub = f'🇯🇵 午後の東京は、高市勝利、円防衛の信頼回復、対米交渉カードの3点が新材料となり、油高と輸入コスト懸念を一部相殺 · SoftBankのLY交渉は、企業が自前で握れる国内優位を求めていることを示した · 世界では米雇用が下支えとなる一方、欧州は関税とエネルギーに苦しみ、ホルムズが依然マクロ全体を動かしている · Health Score: {HEALTH}/100'
    footer = 'CEO Afternoon Briefing · Generated by Sanbot · 2026年5月12日（火）'
    return f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html">EN</a><span class="sep">/</span><a href="ja.html" class="active">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">{WAR_DAY}</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_JA} 午後版</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">日本</a><a href="#global" class="nav-pill">世界</a><a href="#markets" class="nav-pill">市場</a><a href="#predictions" class="nav-pill">予測</a><a href="#bottomline" class="nav-pill">結論</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">日本アップデート</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">世界の動き</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">市場と経済</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">予測</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''


def build_page(path: Path, lang='en'):
    src_html = path.read_text()
    head = src_html.split('<body>')[0] + '<body>\n'
    head = re.sub(r'<title>CEO Briefing — [^<]+</title>', f'<title>CEO Briefing — {TITLE_DATE}</title>', head)
    path.write_text(head + build_body(lang))


build_page(BASE / 'index.html', 'en')
build_page(BASE / 'ja.html', 'ja')
print('updated')
