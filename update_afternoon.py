# -*- coding: utf-8 -*-
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BASE = Path('/Users/xand/.openclaw/workspace/ceo-briefing')
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TODAY_EN = 'Monday, April 27, 2026'
TODAY_JA = '2026年4月27日（月）'
TITLE_DATE = 'Apr 27, 2026'


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
    'yen_spec': gnews("Japan brands yen falls as 'speculative' as Iran war ignites sell-off Reuters"),
    'yen_threat': gnews('Japan steps up yen intervention threats, signals rate-hike chance Reuters'),
    'nikkei_threat': gnews("Japan's record bull run under threat as Mideast war clouds earnings season Reuters"),
    'takaichi_budget': gnews('Japan PM Takaichi rules out extra budget for now Reuters'),
    'core_infl': gnews("Japan's core inflation stays below BOJ target, energy risks grow Reuters"),
    'boj_soft': gnews('Bank of Japan seen dropping hawkish signs even as it keeps rates steady Reuters'),
    'boj_holdoff': gnews('Exclusive BOJ is likely to hold off raising rates in April sources say Reuters'),
    'nojima': gnews("Japan's Nojima to buy Hitachi's consumer appliances unit for more than $630 million Nikkei reports Reuters"),
    'lower_auto_tariffs': gnews('Exclusive Trump signs order to bring lower Japanese auto tariffs into effect Reuters'),
    'stocks_lower': gnews('Oil surges, stocks end lower on worries about tenuous US-Iran ceasefire Reuters'),
    'pg_hit': gnews('P&G warns of $1 billion profit hit in fiscal 2027 from higher oil prices Reuters'),
    'canada_tariffs': gnews('Canada will respond to Trump auto tariffs with its own trade actions Reuters'),
    'eu_95b': gnews('EU sets out possible 95-billion-euro response to US tariffs Reuters'),
    'two_speed_eu': gnews("Germany pushes for 'two-speed' Europe with new bloc of six leading economies Reuters"),
    'ecb_energy': gnews("Energy crisis raises concerns for financial stability ECB's Panetta warns Reuters"),
    'china_fuel_export_ban': gnews("China's fuel export ban to further tighten Asia supply Reuters"),
    'asean_pact': gnews('China and ASEAN hit by US tariffs sign upgraded free trade pact Reuters'),
    'india_oil': gnews('India rupee, bonds under strain on elevated oil Fed guidance in focus Reuters'),
    'sk_hynix': gnews('SK Hynix shares rally 7% to a record high beating Samsung\'s 2.5% gain Reuters'),
    'worldbank_growth': gnews('Middle East war to cut growth deliver cascading impact World Bank chief says Reuters'),
    'trump_choices': gnews('One month into Iran war only hard choices for Trump Reuters'),
    'flights_cancel': gnews('Airlines cancel flights amid Middle East conflict Reuters'),
    'lula_trump': gnews("Brazil's Lula assails Trump threats says leaders should seek respect Reuters"),
    'mercosur_canada': gnews('Mercosur and Canada near free-trade agreement with April talks Reuters'),
    'chile_us': gnews('Chile US to sign mining and security agreements Reuters'),
    'australia_vanuatu': gnews('Australia discusses security aid with Vanuatu amid competition with China Reuters'),
    'iranian_players_aus': gnews("Five Iranian women's soccer players granted humanitarian visas in Australia Reuters"),
    'ecopetrol_brava': gnews("Colombia's Ecopetrol to buy 26% stake in Brazil's Brava seeks majority control Reuters"),
    'yahoo': {'url': 'https://finance.yahoo.com/', 'source': 'Yahoo Finance', 'title': 'Yahoo Finance', 'image': ''},
}

japan = [
    {
        'tag': '🇯🇵 JAPAN · MARKET CLOSE',
        'headline': 'Japan’s bull run looked shakier by the close because the Middle East shock started to cloud earnings assumptions that had supported Tokyo all morning.',
        'body': '<strong>Why it happened:</strong> investors spent the afternoon repricing two opposing forces at once: tech and governance optimism on one side, and oil-driven margin risk on the other. The Nikkei did not simply move on sentiment. It softened because higher crude and a more fragile yen raised the odds that imported-cost pressure will start eating into earnings just as the reporting season broadens.',
        'sources': [src['nikkei_threat'], src['stocks_lower']],
    },
    {
        'tag': '🇯🇵 JAPAN · FX / POLICY SIGNAL',
        'headline': 'Tokyo branded the yen move “speculative” and escalated intervention threats because war-driven dollar demand was pushing the currency down faster than policymakers could ignore.',
        'body': '<strong>Why it happened:</strong> the causal chain is clear: stalled diplomacy kept oil high, higher oil pushed money into the dollar, and that dollar bid intensified yen weakness. Officials reacted because once they believe one-way positioning is amplifying a move beyond fundamentals, defending credibility becomes almost as important as defending the currency level itself.',
        'sources': [src['yen_spec'], src['yen_threat']],
    },
    {
        'tag': '🇯🇵 JAPAN · FISCAL POLICY',
        'headline': 'Prime Minister Takaichi ruled out an extra budget for now because Tokyo is trying to conserve fiscal ammunition until it knows whether the energy shock becomes a lasting demand problem.',
        'body': '<strong>Why it happened:</strong> if the government spent immediately, it would risk using scarce fiscal space on a shock that may still mutate. Holding back tells markets that Tokyo sees the first-round oil hit as painful but not yet severe enough to justify another major package. The cause is strategic sequencing, not passivity.',
        'sources': [src['takaichi_budget']],
    },
    {
        'tag': '🇯🇵 JAPAN · INFLATION',
        'headline': 'Japan’s core inflation stayed below target even as energy risks worsened, because domestic demand remains too soft to fully transmit the imported oil shock into broad underlying prices.',
        'body': '<strong>Why it happened:</strong> this is the policy trap in one sentence: oil and the yen are pushing headline pressure up, but household demand is not strong enough to make that inflation self-sustaining. That is why the inflation miss matters. It explains why the BOJ cannot simply answer the energy shock with a much more hawkish stance.',
        'sources': [src['core_infl']],
    },
    {
        'tag': '🇯🇵 JAPAN · BOJ WATCH',
        'headline': 'The BOJ is leaning toward softer guidance and another hold because it sees war-fuelled inflation risk rising without the kind of demand strength that would justify a clean rate-hike message.',
        'body': '<strong>Why it happened:</strong> imported inflation alone is not enough for a confident tightening cycle. The central bank is hesitating because raising rates into a fragile consumer backdrop could deepen the slowdown before wages and consumption have fully caught up. In other words, the cause of caution is not complacency, but an asymmetric growth risk.',
        'sources': [src['boj_soft'], src['boj_holdoff']],
    },
    {
        'tag': '🇯🇵 JAPAN · CORPORATE',
        'headline': 'Nojima’s move on Hitachi’s consumer-appliance unit and Trump’s lower auto-tariff order both mattered because they showed Japanese corporates are still trying to lock in strategic advantages while the macro backdrop darkens.',
        'body': '<strong>Why it happened:</strong> Nojima’s deal logic is defensive expansion, buying scale in a category where distribution and margin discipline matter more when consumers get cautious. The US tariff order matters for the opposite reason, because it offers Japanese automakers partial relief just as energy and currency stress threaten costs elsewhere. Both are responses to the same cause: companies want controllable wins while the geopolitical tape stays unstable.',
        'sources': [src['nojima'], src['lower_auto_tariffs']],
    },
]

global_regions = {
    'North America': [
        ('North America', 'US risk assets lost altitude because traders no longer believed a shaky US-Iran ceasefire narrative would quickly drain the oil premium from markets.', '<strong>Why it happened:</strong> when diplomacy looks fragile, investors stop treating higher crude as temporary noise and start pricing the knock-on effects on inflation, margins, and Fed flexibility. That is why stocks slipped even after a relatively resilient morning setup.', [src['stocks_lower']]),
        ('North America', 'P&G warned higher oil could carve $1 billion out of fiscal 2027 profit because freight, packaging, and petrochemical inputs all become more expensive when crude stays elevated.', '<strong>Why it happened:</strong> this is second-round inflation in corporate form. Energy did not just lift pump prices, it flowed into logistics and raw-material costs. The warning matters because it shows the war shock is now hitting earnings math, not just macro commentary.', [src['pg_hit']]),
        ('North America', 'Canada prepared retaliatory trade action because Trump’s auto tariffs were seen as a direct threat to an integrated North American manufacturing chain.', '<strong>Why it happened:</strong> Ottawa is reacting because standing still would let tariff pressure reshape investment decisions against Canadian plants. The cause is defensive industrial policy: once the US weaponizes auto access, Canada has to answer to preserve bargaining leverage.', [src['canada_tariffs']]),
    ],
    'Europe': [
        ('Europe', 'The EU laid out a possible 95 billion euro response to US tariffs because Brussels concluded that a credible deterrent is the only way to slow further trade escalation.', '<strong>Why it happened:</strong> the bloc is trying to change Washington’s cost-benefit calculation. If Europe looked passive, tariff threats would multiply. The cause of the package is therefore bargaining strategy, not protectionism for its own sake.', [src['eu_95b']]),
        ('Europe', 'Germany pushed a “two-speed Europe” concept because Berlin wants a smaller core group able to move faster on defence, industry, and fiscal coordination while the wider EU remains politically slower.', '<strong>Why it happened:</strong> repeated crises have exposed how hard it is to get 27 states moving at the same pace. The proposal is a reaction to institutional drag, with the cause being urgency around competitiveness and security rather than treaty idealism.', [src['two_speed_eu']]),
        ('Europe', 'ECB officials kept stressing financial-stability risk because the new energy squeeze threatens to revive inflation stress while also tightening credit and growth conditions.', '<strong>Why it happened:</strong> policymakers are worried that energy shocks do not stay in one lane. They can lift prices, hurt banks’ borrowers, and unsettle bond markets at the same time. That three-part causal chain is why the ECB tone remains cautious.', [src['ecb_energy']]),
    ],
    'Asia ex-Japan': [
        ('Asia ex-Japan', 'China’s fuel export ban tightened the regional supply picture because fewer Chinese barrels available abroad force importers across Asia to compete harder for replacement product.', '<strong>Why it happened:</strong> Beijing is prioritizing domestic stability, and that choice matters regionally because China is too large a refining player to withdraw supply without moving prices elsewhere. The cause is policy insulation at home, with inflation consequences abroad.', [src['china_fuel_export_ban']]),
        ('Asia ex-Japan', 'China and ASEAN upgraded their trade pact because both sides want to offset US tariff pressure by deepening regional demand and supply-chain links.', '<strong>Why it happened:</strong> the agreement is a direct response to external pressure. When access to the US becomes less reliable, the economic incentive to make Asia trade more with itself gets much stronger.', [src['asean_pact']]),
        ('Asia ex-Japan', 'India’s rupee and bond market stayed under strain because elevated oil prices threaten both its import bill and the inflation path the RBI needs for easier policy.', '<strong>Why it happened:</strong> India imports a large share of its energy, so higher crude worsens the current account first and monetary flexibility second. That is why the market reaction was not just about FX, but also about rates.', [src['india_oil']]),
    ],
    'Middle East & Africa': [
        ('Middle East & Africa', 'The World Bank warned the war will cut growth because a prolonged energy-and-shipping shock acts like a tax on both importers and corporate investment plans.', '<strong>Why it happened:</strong> once higher fuel, insurance, and routing costs persist, they spread from commodity markets into trade volumes, consumer spending, and capital expenditure. The growth hit comes from that cascading chain, not from oil alone.', [src['worldbank_growth']]),
        ('Middle East & Africa', 'Washington faced only hard choices one month into the Iran war because every available path now carries a different mix of military, inflation, and political risk.', '<strong>Why it happened:</strong> the early hope of a cheap, quick stabilisation faded. The cause of the harder US posture is that each additional week of conflict raises the cost of backing down while also raising the cost of escalation.', [src['trump_choices']]),
        ('Middle East & Africa', 'Airlines kept cancelling flights because the conflict has made air corridors and insurance assumptions too unstable for normal scheduling.', '<strong>Why it happened:</strong> carriers are not reacting to a single incident. They are responding to compounded risk from airspace restrictions, crew safety, fuel costs, and schedule reliability. That is why disruptions are lasting longer.', [src['flights_cancel']]),
    ],
    'Latin America': [
        ('Latin America', 'Lula rebuked Trump’s threats because Brazil sees public resistance as necessary to avoid looking strategically subordinate in a harsher trade-and-security climate.', '<strong>Why it happened:</strong> Brazil’s government believes visible pushback protects domestic political legitimacy and strengthens its bargaining hand abroad. The cause is not only ideology, but also coalition management at home.', [src['lula_trump']]),
        ('Latin America', 'Mercosur moved closer to a Canada trade deal because both sides want new commercial channels before US tariff politics squeezes global trade flows even further.', '<strong>Why it happened:</strong> diversification becomes more valuable when the biggest markets turn less predictable. The cause of faster talks is risk hedging: locking in alternative demand while there is still negotiating room.', [src['mercosur_canada']]),
        ('Latin America', 'Chile prepared mining and security deals with the US because critical minerals have become inseparable from broader geopolitical alignment.', '<strong>Why it happened:</strong> Washington wants secure copper and lithium-linked partnerships, and Chile wants capital plus strategic relevance. The cause is the same on both sides: supply security now drives diplomacy.', [src['chile_us']]),
    ],
    'Oceania': [
        ('Oceania', 'Australia deepened talks with Vanuatu because Canberra does not want China converting development ties into another durable strategic foothold in the Pacific.', '<strong>Why it happened:</strong> aid and security are being bundled together because influence in the Pacific is now treated as a hard-security issue, not only a diplomatic one. That competitive logic is the cause of the renewed push.', [src['australia_vanuatu']]),
        ('Oceania', 'Australia’s humanitarian visas for five Iranian women footballers stood out because conflict displacement and gender persecution are increasingly colliding with the region’s migration politics.', '<strong>Why it happened:</strong> Canberra acted because the athletes’ case fit both a humanitarian narrative and a values-signalling opportunity. The cause was not routine processing, but the specific political salience of the war and women’s rights.', [src['iranian_players_aus']]),
    ],
}

japan_ja = [
    ('🇯🇵 日本・大引け', '日本株の強気相場は午後にやや不安定さを増した。中東ショックが、朝まで相場を支えていた業績期待に影を落とし始めたからだ。', '<strong>なぜそうなったか：</strong>午後の投資家は、テックとガバナンス改革への期待と、原油高による利益率悪化リスクを同時に再計算した。つまり単なる地合い悪化ではなく、「油高と円安が本格的に業績へ効くのでは」という因果が意識された。', [src['nikkei_threat'], src['stocks_lower']]),
    ('🇯🇵 日本・為替/政策シグナル', '政府が円安を「投機的」と表現し、介入警戒を強めた。戦争起点のドル買いで、許容しにくい速度の円売りが進んだからだ。', '<strong>なぜ強い言い方か：</strong>イラン情勢の停滞で原油が高止まりし、その結果としてドル需要が強まり、円安が加速した。当局はファンダメンタルズ以上に投機ポジションが膨らんだと見ているため、口先ではなく実際の介入可能性を市場に意識させたい。', [src['yen_spec'], src['yen_threat']]),
    ('🇯🇵 日本・財政政策', '高市首相が追加補正を当面見送ったのは、エネルギーショックが一時的か長期化するかを見極めるまで、財政余力を温存したいからだ。', '<strong>なぜ今は出さないか：</strong>ここで早く使いすぎると、本当に需要悪化が深まった局面で打つ手が減る。今回の判断は消極策ではなく、「まずショックの性質を見極める」という順番の問題。', [src['takaichi_budget']]),
    ('🇯🇵 日本・インフレ', 'コアインフレは日銀目標を下回った一方で、エネルギーリスクは上がった。原油高の輸入インフレがあっても、内需がまだ十分強くないからだ。', '<strong>なぜ重要か：</strong>「油高と円安で見出しの物価は上がるが、需要が弱いため基調インフレは伸び切らない」というねじれが続いている。これが、日銀が簡単にタカ派へ振れにくい理由そのもの。', [src['core_infl']]),
    ('🇯🇵 日本・日銀', '日銀は据え置きと慎重ガイダンスに傾いている。戦争起点のインフレ圧力は増しても、需要の裏付けが弱く、強い利上げメッセージを出しにくいからだ。', '<strong>なぜ慎重か：</strong>輸入インフレだけで引き締めを急ぐと、消費が弱い段階で景気をさらに冷やしかねない。つまり日銀の慎重姿勢は楽観ではなく、成長下振れリスクへの配慮。', [src['boj_soft'], src['boj_holdoff']]),
    ('🇯🇵 日本・企業戦略', 'ノジマの買収案件と米国の対日自動車関税緩和は、マクロが悪化する中でも日本企業が取りに行ける優位を急いで確保していることを示した。', '<strong>なぜこの2本が効くか：</strong>ノジマは消費が鈍る局面でも採算を取りやすい領域で規模を取りにいき、関税緩和は自動車各社にコスト圧迫への部分的な逃げ道を与える。どちらも「外部環境は読めないから、コントロールできる勝ち筋を先に固める」という同じ因果で動いている。', [src['nojima'], src['lower_auto_tariffs']]),
]

global_regions_ja = {
    '北米': [
        ('北米', '米リスク資産は失速した。脆い米イラン停戦期待では、原油プレミアムがすぐ消えないと市場が判断したからだ。', '<strong>なぜ下げたか：</strong>外交が不安定だと、原油高は一時ノイズではなく、インフレ・利益率・FRBの自由度に効く問題として再評価される。そのため株は午後に重くなった。', [src['stocks_lower']]),
        ('北米', 'P&Gが2027年度利益に10億ドルの逆風を警告した。原油高が物流、包装、石化原料へ連鎖してコストを押し上げるからだ。', '<strong>なぜ象徴的か：</strong>エネルギー高がマクロの話から企業収益の話へ移ったことを示している。つまり戦争ショックが「見出し」から「決算の算式」に変わり始めた。', [src['pg_hit']]),
        ('北米', 'カナダが対抗措置を準備したのは、トランプの自動車関税が北米一体の製造サプライチェーンを直撃すると見たからだ。', '<strong>なぜ応戦か：</strong>何もしなければ投資判断が米国に偏り、カナダ工場の立場が悪くなる。つまり目的は報復そのものではなく、交渉力と産業基盤の防衛。', [src['canada_tariffs']]),
    ],
    '欧州': [
        ('欧州', 'EUが950億ユーロ規模の対米対応案を示したのは、報復能力を見せること自体が追加関税の抑止になると判断したからだ。', '<strong>なぜこの規模か：</strong>受け身に見えるほど米国の圧力は強まりやすい。ブリュッセルは、先にコストを見せることでワシントンの計算を変えたい。', [src['eu_95b']]),
        ('欧州', 'ドイツが「二速度の欧州」を押し出した。防衛、産業、財政で、27カ国全員が同じ速度で動くのは遅すぎると感じているからだ。', '<strong>なぜ今か：</strong>危機が続くほど制度の遅さが目立つ。ベルリンは理想論より実行速度を優先し始めており、その原因は競争力と安全保障への焦り。', [src['two_speed_eu']]),
        ('欧州', 'ECBが金融安定リスクを強調し続けたのは、エネルギー再ショックが物価だけでなく信用と成長にも同時に効き得るからだ。', '<strong>なぜ慎重か：</strong>油高はインフレ再燃、借り手の負担増、債券市場の不安定化を同時に招き得る。ECBはその三重の因果を警戒している。', [src['ecb_energy']]),
    ],
    'アジア（日本除く）': [
        ('アジア（日本除く）', '中国の燃料輸出制限で域内需給がさらに引き締まった。中国が国内安定を優先し、周辺国向け供給が減るからだ。', '<strong>なぜ広がるか：</strong>中国は精製品市場で大きすぎる存在なので、輸出を絞るだけで他国の調達競争が激しくなる。原因は国内防衛策だが、影響はアジア全域に波及する。', [src['china_fuel_export_ban']]),
        ('アジア（日本除く）', '中国とASEANが通商協定を深めたのは、米関税圧力への対抗として域内需要と供給網を厚くしたいからだ。', '<strong>なぜ進むか：</strong>米国向けアクセスの不確実性が高いほど、アジア同士で回す経済圏の価値が上がる。つまり外圧が地域統合を加速させている。', [src['asean_pact']]),
        ('アジア（日本除く）', 'インドのルピーと債券が重いのは、原油高が輸入代金とインフレ見通しの両方を悪化させるからだ。', '<strong>なぜ債券まで効くか：</strong>原油輸入国のインドでは、油高が経常赤字を悪化させるだけでなく、利下げ余地も狭める。そのため通貨だけでなく金利市場も同時に圧迫される。', [src['india_oil']]),
    ],
    '中東・アフリカ': [
        ('中東・アフリカ', '世界銀行が成長下振れを警告したのは、戦争がエネルギーと物流の持続的なコスト増として世界経済に波及しているからだ。', '<strong>なぜ成長に効くか：</strong>燃料、保険、迂回輸送が高止まりすると、貿易量、個人消費、設備投資の順に痛んでいく。成長鈍化はその連鎖の結果。', [src['worldbank_growth']]),
        ('中東・アフリカ', 'イラン戦争1カ月で米国の選択肢が苦しくなった。どの道を選んでも軍事・物価・政治コストが膨らむ段階に入ったからだ。', '<strong>なぜ難化したか：</strong>短期収束への期待が剥がれ、引くにも進むにも高くつく局面に変わった。時間の経過そのものが政策コストを増やしている。', [src['trump_choices']]),
        ('中東・アフリカ', '航空各社の欠航が続くのは、空域・保険・乗員安全・燃料費の不確実性が通常運航を成り立たせにくくしているからだ。', '<strong>なぜ長引くか：</strong>単発事故への反応ではなく、複数リスクの同時上昇への対応だから。だからこそ混乱は一時的に終わりにくい。', [src['flights_cancel']]),
    ],
    'ラテンアメリカ': [
        ('ラテンアメリカ', 'ルラ大統領がトランプを公然と批判したのは、強硬姿勢を見せないと国内政治でも対外交渉でも弱く見えるからだ。', '<strong>なぜ強く言うか：</strong>対外的な自立姿勢は国内支持の維持にも効く。今回の発言は理念だけでなく、交渉力と政権運営の防衛でもある。', [src['lula_trump']]),
        ('ラテンアメリカ', 'メルコスールとカナダのFTA接近は、米関税政治が強まる前に代替販路を増やしたいからだ。', '<strong>なぜ急ぐか：</strong>主要市場の予見性が落ちるほど、新しい需要先を確保する価値は高くなる。交渉加速の原因はリスク分散。', [src['mercosur_canada']]),
        ('ラテンアメリカ', 'チリと米国の鉱業・安全保障協定は、重要鉱物が外交と安全保障の中心資産になったからだ。', '<strong>なぜ今重要か：</strong>米国は安定供給を求め、チリは資本と戦略的重要性を得たい。供給安全保障が両者を近づけている。', [src['chile_us']]),
    ],
    'オセアニア': [
        ('オセアニア', '豪州がバヌアツとの安全保障・支援協議を深めたのは、中国に太平洋で新たな足場を許したくないからだ。', '<strong>なぜ支援と安全保障を一体化するか：</strong>太平洋の影響力争いが、もはや外交だけでなくハードな安全保障問題になっているため。', [src['australia_vanuatu']]),
        ('オセアニア', '豪州がイラン人女子サッカー選手5人に人道ビザを認めたのは、戦争避難と女性の権利問題が重なり、政治的にも象徴性が高かったからだ。', '<strong>なぜ目立つか：</strong>通常処理ではなく、戦争とジェンダー抑圧が交差する事案として扱われたため。人道対応であると同時に価値観のシグナルでもある。', [src['iranian_players_aus']]),
    ],
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

market_sources = [
    src['stocks_lower'],
    src['worldbank_growth'],
    src['china_fuel_export_ban'],
    src['yahoo'],
]


def build_body(lang='en'):
    if lang == 'en':
        japan_cards = '\n'.join(story_card(x['tag'], x['headline'], x['body'], x['sources']) for x in japan)
        global_cards = []
        for _, items in global_regions.items():
            for tag, headline, body, sources in items:
                global_cards.append(story_card(tag, headline, body, sources))
        global_cards = '\n'.join(global_cards)
        markets = '\n'.join([
            table_card('EQUITIES', 'End-of-day equity snapshot', ['Index', 'Level', 'Daily', 'Weekly', 'Monthly', 'YTD'], EQ_ROWS, '<strong>Why the bigger moves happened:</strong> today\'s most important equity driver was whether each market was seen as an earnings beneficiary or an oil victim. Japan held up better where tech and tariff relief cushioned the blow. Markets tied more directly to energy-import stress or tariff retaliation suffered more. Any move above 2% should be read through that chain first.', market_sources),
            table_card('FX & RATES', 'Currency and rate pressure points', ['Instrument', 'Level', 'Daily', 'Weekly', 'Monthly', 'YTD'], FX_ROWS, '<strong>Why it matters:</strong> USD/JPY remains the fastest read on Japan\'s policy stress because a weaker yen helps exporters but worsens imported inflation. DXY and Treasuries matter because the longer oil stays high, the harder it becomes for central banks to sound relaxed.', market_sources),
            table_card('COMMODITIES & CRYPTO', 'Commodity and digital-asset close', ['Asset', 'Price', 'Daily', 'Weekly', 'Monthly', 'YTD'], CMD_ROWS, '<strong>Big mover logic:</strong> if crude is up more than 2%, the cause is still war-risk pricing plus tighter regional fuel supply after China\'s export restrictions. If silver or crypto move more than 2%, the likely causes are dollar repricing and changing inflation-hedge demand rather than isolated sector news.', market_sources),
            '''        <article class="card fade-in" data-image="'''+(market_sources[0].get('image',''))+'''"><span class="card-tag">HEALTH SCORE</span><h3 class="card-headline">51/100, still functioning, but the afternoon got materially less forgiving.</h3><p class="card-body"><strong>Why 51:</strong> Japan still has real supports, especially tech earnings, selective tariff relief, and capital-discipline stories. But the afternoon balance worsened because the yen stayed under pressure, oil remained elevated, and more companies began translating geopolitics into profit warnings and growth downgrades. That combination keeps markets investable, but noticeably more brittle than they looked this morning.</p><div class="card-sources">\n'''+source_links(market_sources)+'''\n          </div></article>'''
        ])
        predictions = '''        <article class="card fade-in collapsible" data-image=""><span class="card-tag">TOMORROW</span><h3 class="card-headline">Watch whether Japanese policymakers escalate from verbal yen defence to something more concrete if dollar strength extends.</h3><div class="tap-hint">Tap to expand</div><p class="card-body"><strong>Why it matters:</strong> if USD/JPY keeps rising while core inflation remains soft, Tokyo may feel forced to defend the currency even without a clean BOJ tightening backdrop. That would turn Japan from a passive observer of the oil shock into an active policy battleground.</p></article>
        <article class="card fade-in collapsible" data-image=""><span class="card-tag">WEEK AHEAD</span><h3 class="card-headline">The key macro test is whether higher oil stays a market story or becomes a broad earnings-and-demand downgrade cycle.</h3><div class="tap-hint">Tap to expand</div><p class="card-body"><strong>Why it matters:</strong> once consumer staples, airlines, importers, and central banks are all talking about the same energy shock, the market stops pricing headlines and starts pricing duration. If that happens, volatility rises because the damage window gets easier to quantify and harder to dismiss.</p></article>'''
        bottom_line = 'The afternoon message was harsher than the morning one. <strong>Japan still looked relatively resilient, but only because investors could still point to specific offsets such as tech earnings, selective tariff relief, and corporate action.</strong> Outside Japan, the tone worsened because the oil shock kept spreading from geopolitics into currencies, inflation expectations, earnings guidance, and trade retaliation. <strong>Bottom line:</strong> the day\'s new information did not say “panic,” but it clearly said “this shock is broadening.”'
        sub = '🇯🇵 Tokyo spent the afternoon balancing tech resilience against a weaker yen, softer core inflation, and a BOJ that still cannot tighten cleanly into fragile demand · Takaichi held fire on fiscal stimulus while Japanese corporates chased controllable wins through M&A and tariff relief · Globally, the oil shock spread into profit warnings, tariff retaliation, ECB stability fears, and a darker World Bank growth message · Health Score: 51/100'
        footer = 'CEO Afternoon Briefing · Generated by Sanbot · Monday, April 27, 2026'
        return f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html" class="active">EN</a><span class="sep">/</span><a href="ja.html">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">56</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_EN} — Afternoon Edition</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">Japan</a><a href="#global" class="nav-pill">Global</a><a href="#markets" class="nav-pill">Markets</a><a href="#predictions" class="nav-pill">Predictions</a><a href="#bottomline" class="nav-pill">Bottom Line</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">Japan Update — In Depth</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">Global — By Continent</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">Markets & Economy</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">Predictions</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''

    japan_cards = '\n'.join(story_card(t, h, b, s, ja=True) for t, h, b, s in japan_ja)
    global_cards = []
    for _, items in global_regions_ja.items():
        for tag, headline, body, sources in items:
            global_cards.append(story_card(tag, headline, body, sources, ja=True))
    global_cards = '\n'.join(global_cards)
    markets = '\n'.join([
        table_card('株式', '引け後マーケット一覧', ['指数', '水準', '日次', '週次', '月次', '年初来'], EQ_ROWS, '<strong>大きな値動きの因果：</strong>今日は各市場が「業績で守られる側」か「油高で傷む側」かで差がついた。日本はテックと関税緩和が下支えし、エネルギー輸入負担や報復関税に近い市場ほど弱かった。2%超の動きはまずこの因果で読むべき。', market_sources),
        table_card('為替・金利', '通貨と金利の要点', ['指標', '水準', '日次', '週次', '月次', '年初来'], FX_ROWS, '<strong>なぜ重要か：</strong>USD/JPYは日本の政策ストレスを最も早く映す。円安は輸出株を助ける一方で輸入インフレを悪化させる。DXYと米金利は、油高が長引くほど中銀が楽観を語りにくくなることを示す。', market_sources),
        table_card('商品・暗号資産', '商品とデジタル資産の引け', ['資産', '価格', '日次', '週次', '月次', '年初来'], CMD_ROWS, '<strong>大きく動く理由：</strong>原油が2%以上動くなら、主因は戦争リスクと中国の輸出制限による域内燃料需給の引き締まり。銀や暗号資産の2%超変動は、今日はドル再評価とインフレヘッジ需要の変化で読むのが自然。', market_sources),
        '''        <article class="card fade-in" data-image="'''+(market_sources[0].get('image',''))+'''"><span class="card-tag">ヘルススコア</span><h3 class="card-headline">51/100、まだ機能しているが、午後の相場は明確に扱いづらくなった。</h3><p class="card-body"><strong>なぜ51か：</strong>日本にはテック決算、部分的な関税緩和、資本効率改善といった支えがまだある。ただし午後は、円安圧力、油高、高コストの企業収益化、世界銀行の成長警告が重なり、朝より相場の脆さが増した。つまり崩壊ではないが、ショックの広がりは無視できない。</p><div class="card-sources">\n'''+source_links(market_sources)+'''\n          </div></article>'''
    ])
    predictions = '''        <article class="card fade-in collapsible" data-image=""><span class="card-tag">明日</span><h3 class="card-headline">ドル高が続けば、日本の為替防衛が口先から一段具体化するかを注視。</h3><div class="tap-hint">タップして展開</div><p class="card-body"><strong>なぜ注目か：</strong>コアインフレが弱いままUSD/JPYが上がると、日銀は強く締めにくい一方で、政府は通貨防衛を迫られる。そうなると日本は受け身ではなく、政策の主戦場になる。</p></article>
    <article class="card fade-in collapsible" data-image=""><span class="card-tag">今週</span><h3 class="card-headline">高い原油が市場ニュースで終わるのか、広範な業績・需要下方修正へ変わるのかが最大の分岐点。</h3><div class="tap-hint">タップして展開</div><p class="card-body"><strong>なぜそこか：</strong>生活必需品、航空、輸入国、中銀が同じショックを語り始めると、市場は見出しではなく「長さ」を値付けするようになる。そこからボラティリティは一段上がりやすい。</p></article>'''
    bottom_line = '午後に見えた新しい事実は、<strong>日本が相対的に強いとしても、それは安全だからではなく、まだ買う理由が残っているから</strong>ということだ。世界全体では、油高ショックが為替、物価、企業収益、通商報復、成長見通しへと広がった。<strong>結論：</strong>まだパニックではないが、ショックは確実に多方面へ波及している。'
    sub = '🇯🇵 日本は、テックの底堅さと円安・低コアインフレ・慎重な日銀の綱引きが午後の主題だった · 高市首相は補正を温存し、企業はM&Aと関税緩和で取りに行ける優位を確保しにいった · 世界では油高ショックが収益警告、報復関税、ECBの安定懸念、世銀の成長警戒へ広がった · Health Score: 51/100'
    footer = 'CEO Afternoon Briefing · Generated by Sanbot · 2026年4月27日（月）'
    return f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html">EN</a><span class="sep">/</span><a href="ja.html" class="active">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">56</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_JA} 午後版</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">日本</a><a href="#global" class="nav-pill">世界</a><a href="#markets" class="nav-pill">市場</a><a href="#predictions" class="nav-pill">予測</a><a href="#bottomline" class="nav-pill">結論</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">日本アップデート</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">世界の動き</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">市場と経済</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">予測</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''


def build_page(path: Path, lang='en'):
    src_html = path.read_text()
    head = src_html.split('<body>')[0] + '<body>\n'
    body = build_body(lang)
    page = re.sub(r'<title>CEO Briefing — [^<]+</title>', f'<title>CEO Briefing — {TITLE_DATE}</title>', head) + body
    path.write_text(page)


build_page(BASE / 'index.html', 'en')
build_page(BASE / 'ja.html', 'ja')
print('updated')
