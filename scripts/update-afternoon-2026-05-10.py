# -*- coding: utf-8 -*-
import html, re, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path
import requests

BASE = Path('/Users/xand/.openclaw/workspace/ceo-briefing')
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TODAY_EN = 'Sunday, May 10, 2026'
TODAY_JA = '2026年5月10日（日）'
TITLE_DATE = 'May 10, 2026'
WAR_DAY = '69'
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
    return (name, f'{last:,.{digits}f}{suffix}', fmt_pct((last / prev - 1) * 100), fmt_pct((last / week - 1) * 100), fmt_pct((last / month - 1) * 100), fmt_pct((last / ytd - 1) * 100))


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
    'japan_bonds': gnews("Decisive win for Japan PM Takaichi may be best scenario for bonds yen Reuters"),
    'japan_stocks': gnews("Japan stocks soar super-long bonds steady in nod to Takaichi's responsible stimulus Reuters"),
    'japan_taxcut': gnews('Japan may struggle to calm markets tripped up by Takaichis taboo tax cut Reuters'),
    'yen_jump': gnews('Yen jumps abruptly as speculation about Japanese intervention swirls Reuters'),
    'japan_us': gnews('Japan keeps US close as it signals unlimited yen defence Reuters'),
    'line': gnews('South Korea Naver exploring options including stake sale in Line operator Reuters'),
    'us_mixed': gnews('Stocks mixed dollar down as investors digest US job growth chipmaker strength and elevated oil Reuters'),
    'eu_tariffs': gnews('US to move forward with plans to hike EU car tariffs Reuters'),
    'truce_cracks': gnews('US stocks end lower oil climbs as cracks appear in fragile US-Iran truce Reuters'),
    'china_exports': gnews('China April exports rebound strongly trade surplus widens ahead of Trump visit Reuters'),
    'jimmy_lai': gnews('China critic Jimmy Lai sentenced to 20 years in jail after landmark Hong Kong trial Reuters'),
    'india_credit': gnews('India approves $1.9 billion credit guarantee to support businesses hit by Middle East crisis Reuters'),
    'airlines': gnews('Airlines cancel flights in response to Middle East conflict Reuters'),
    'jetfuel': gnews('Airlines tackle fuel cost surge with price hikes outlook cuts Reuters'),
    'brazil': gnews("Brazil's Lula reports progress in relations with US after talks with Trump Reuters"),
    'vanuatu': gnews('Australia Vanuatu security agreement to be delayed Reuters'),
    'yahoo': {'url': 'https://finance.yahoo.com/', 'source': 'Yahoo Finance', 'title': 'Yahoo Finance', 'image': ''},
}

EQ_ROWS = [market_row('Nikkei 225', '^N225'), market_row('S&P 500', '^GSPC'), market_row('Dow Jones', '^DJI'), market_row('Nasdaq', '^IXIC'), market_row('Euro Stoxx 50', '^STOXX50E'), market_row('Shanghai Comp', '000001.SS'), market_row('Sensex', '^BSESN'), market_row('Bovespa', '^BVSP', 0), market_row('ASX 200', '^AXJO')]
FX_ROWS = [market_row('USD/JPY', 'JPY=X', 3), market_row('EUR/USD', 'EURUSD=X', 4), market_row('DXY', 'DX-Y.NYB', 3), market_row('US 10Y Treasury', '^TNX', 3, '%'), market_row('US 2Y Treasury', '^IRX', 3, '%')]
CMD_ROWS = [market_row('WTI Crude', 'CL=F'), market_row('Brent Crude', 'BZ=F'), market_row('Gold', 'GC=F'), market_row('Silver', 'SI=F', 3), market_row('Bitcoin', 'BTC-USD'), market_row('Ethereum', 'ETH-USD')]

nikkei_level, nikkei_day = EQ_ROWS[0][1], EQ_ROWS[0][2]
spx_level, spx_day = EQ_ROWS[1][1], EQ_ROWS[1][2]
usdjpy_level, usdjpy_day = FX_ROWS[0][1], FX_ROWS[0][2]
wti_level, wti_day = CMD_ROWS[0][1], CMD_ROWS[0][2]

japan = [
    {'tag': '🇯🇵 JAPAN · POLITICS / BONDS', 'headline': 'Tokyo’s biggest fresh afternoon shift was that Takaichi’s decisive win started being read as bond-friendly, not just growth-friendly, because investors now think any stimulus push will come with enough fiscal discipline to avoid a sudden super-long JGB tantrum.', 'body': '<strong>Why it happened:</strong> markets had feared a pure tax-cut shock, but the vote margin reduced coalition noise and made it easier to imagine a more controlled policy package. That changed the causal chain from “political win equals fiscal panic” to “political win could mean cleaner policy execution.”', 'sources': [src['japan_bonds'], src['japan_stocks']]},
    {'tag': '🇯🇵 JAPAN · MARKET CLOSE', 'headline': f'Nikkei finished at {nikkei_level} ({nikkei_day}) because domestic cyclicals benefited from the Takaichi mandate while exporters still had to price the risk that a stronger yen would follow any credible intervention campaign.', 'body': '<strong>Why it happened:</strong> election clarity helped banks, retailers, and rate-sensitive domestic names, but the same clarity also raised the odds of a firmer currency line from Tokyo. That split the market between companies that gain from steadier policy and those that lose if FX tailwinds fade.', 'sources': [src['japan_stocks'], src['yen_jump']]},
    {'tag': '🇯🇵 JAPAN · FX DEFENCE', 'headline': f'USD/JPY trading around {usdjpy_level} ({usdjpy_day}) stayed the afternoon’s most important stress gauge because the yen suddenly looked less like a passive casualty of rate differentials and more like a market Tokyo is prepared to actively police.', 'body': '<strong>Why it happened:</strong> intervention chatter only works when traders think the state is willing to keep paying for it. Today’s abrupt yen jump mattered because it suggested speculators briefly believed officials were ready to escalate from signalling to action.', 'sources': [src['yen_jump'], src['japan_us']]},
    {'tag': '🇯🇵 JAPAN · POLICY RISK', 'headline': 'The market’s other Japan debate shifted toward whether Takaichi can deliver tax cuts without destabilising confidence, because her taboo-tax-cut rhetoric is attractive to households but dangerous if investors start questioning the funding math.', 'body': '<strong>Why it happened:</strong> tax cuts are politically easy to promise after a landslide, but bond investors care about who pays. The afternoon repricing happened because traders started separating “growth support” from “fiscally free,” and that distinction will matter quickly.', 'sources': [src['japan_taxcut'], src['japan_bonds']]},
    {'tag': '🇯🇵 JAPAN · US COORDINATION', 'headline': 'Japan’s tighter public alignment with Washington mattered more after lunch because defending the yen is more believable when it looks like a strategic conversation with the US, not a lonely fight against global dollar strength.', 'body': '<strong>Why it happened:</strong> Tokyo cannot change rate differentials by itself, so it is trying to raise the political cost of testing its red lines. In practice, that means diplomacy is being used as a force multiplier for currency policy.', 'sources': [src['japan_us'], src['yen_jump']]},
    {'tag': '🇯🇵 JAPAN · CORPORATE', 'headline': 'Naver exploring a stake sale in Line operator LY stood out because it could hand Japan’s digital ecosystem a more domestically anchored ownership structure at the same moment the state is becoming more sensitive about data, platforms, and strategic control.', 'body': '<strong>Why it happened:</strong> once geopolitics and regulation get tighter, multinational platform structures stop looking neutral. The deal discussion matters because it reflects a broader move toward keeping key consumer pipes under ownership that is easier for Tokyo to influence.', 'sources': [src['line'], src['japan_us']]},
]

global_regions = {
    'North America': [
        ('North America', f'US equities looked less euphoric by the close, with the S&P 500 at {spx_level} ({spx_day}), because strong job growth and chip optimism had to compete with higher oil and the realisation that a fragile Iran truce still leaves an inflation tail risk.', '<strong>Why it happened:</strong> payroll resilience keeps recession fears down, but that same resilience makes it harder to price fast Fed cuts. Once oil climbed again, the market had to digest a “good growth, bad inflation” mix instead of a clean risk-on story.', [src['us_mixed'], src['truce_cracks']]),
        ('North America', 'The dollar lost some of its earlier momentum because traders started fading the idea that strong data alone can dominate the tape when oil and geopolitics are simultaneously tightening financial conditions.', '<strong>Why it happened:</strong> macro markets reprice differently when growth strength is offset by external shocks. Today the dollar story became less about pure US exceptionalism and more about whether energy risk will slow everyone at once.', [src['us_mixed'], src['truce_cracks']]),
        ('North America', 'The US story stayed globally important because chipmaker strength kept equity leadership narrow, which is usually what happens when investors still trust earnings in a few mega themes but not the entire economy.', '<strong>Why it happened:</strong> concentrated leadership appears when money wants exposure without broad conviction. That is a warning that the market still likes AI cash flows more than it likes the macro backdrop.', [src['us_mixed']]),
    ],
    'Europe': [
        ('Europe', 'Europe remained the clearest tariff victim because Washington’s move toward higher EU car duties hits a sector that carries exports, employment, and political symbolism all at once.', '<strong>Why it happened:</strong> autos are one of the few places where policy pain quickly becomes macro pain in Europe. Tariffs hurt company margins first, then confidence, then already-soft industrial activity.', [src['eu_tariffs']]),
        ('Europe', 'The region also struggled because oil climbed again as the US-Iran truce looked shakier, which is a worse combination for Europe than for the US given Europe’s weaker domestic demand base.', '<strong>Why it happened:</strong> when growth is already soft, imported energy inflation acts like a direct tax. That is why every crack in the truce translated so quickly into regional equity stress.', [src['truce_cracks'], src['eu_tariffs']]),
        ('Europe', 'By the afternoon, Europe was effectively being priced as the place most exposed to both trade fragmentation and expensive energy, which is why it kept lagging despite no single catastrophic headline.', '<strong>Why it happened:</strong> markets punish economies that face multiple medium-sized shocks at once. Europe is carrying tariff risk, external energy dependence, and weak industrial momentum simultaneously.', [src['eu_tariffs'], src['truce_cracks']]),
    ],
    'Asia ex-Japan': [
        ('Asia ex-Japan', 'China’s stronger April export rebound mattered because it suggested Beijing still has enough manufacturing momentum to cushion global demand, at least until oil and shipping disruption start biting harder.', '<strong>Why it happened:</strong> exporters likely front-loaded shipments ahead of Trump-related trade risk and benefitted from still-open channels into major markets. That made China look relatively resilient versus slower Western peers.', [src['china_exports']]),
        ('Asia ex-Japan', 'Hong Kong’s Jimmy Lai sentence mattered regionally because it reminded investors that China’s political risk premium is not fading, even on a day when trade data looked supportive.', '<strong>Why it happened:</strong> strong exports help growth narratives, but security-case headlines reinforce the view that legal and geopolitical friction remain embedded in the China story. Those two forces now coexist rather than cancel out.', [src['jimmy_lai'], src['china_exports']]),
        ('Asia ex-Japan', 'India’s $1.9 billion credit guarantee stood out because New Delhi judged that oil-shock pain could spread from fuel bills into working capital and employment faster than small businesses could absorb.', '<strong>Why it happened:</strong> India imports energy, so a sustained rise in crude immediately pressures transport, input costs, and loan servicing. The package is an attempt to break that causal chain early.', [src['india_credit'], src['airlines']]),
    ],
    'Middle East & Africa': [
        ('Middle East & Africa', f'WTI crude holding near {wti_level} ({wti_day}) showed that traders are still pricing the Middle East as a rolling supply-risk story, not a one-headline event.', '<strong>Why it happened:</strong> once a truce looks fragile, markets price not only outright disruption but also insurance, rerouting, and precautionary inventory demand. Those costs keep crude elevated even without a formal closure.', [src['truce_cracks'], src['airlines']]),
        ('Middle East & Africa', 'Airlines kept cancelling flights because route safety, fuel costs, and scheduling reliability all deteriorated together, turning a geopolitical event into an operational one.', '<strong>Why it happened:</strong> aviation can handle expensive fuel or messy rerouting, but not both plus insurance uncertainty. That is why the sector is reacting with cuts rather than waiting for clarity.', [src['airlines'], src['jetfuel']]),
        ('Middle East & Africa', 'Jet-fuel price pressure also became a wider macro signal because travel disruption is one of the fastest ways for an oil shock to leak into consumer inflation and corporate guidance beyond the region.', '<strong>Why it happened:</strong> higher aviation costs feed tickets, freight, tourism, and business travel all at once. The market cares because this is how a conflict story turns into a broader earnings story.', [src['jetfuel'], src['airlines']]),
    ],
    'Latin America': [
        ('Latin America', 'Lula’s message that relations with Trump improved mattered because Brazil is trying to preserve access to both US diplomacy and commodity demand before the tariff backdrop hardens further.', '<strong>Why it happened:</strong> Brasília knows that strategic ambiguity works best when Washington still sees it as useful. Positive talks are a way to buy room before geopolitical alignment demands intensify.', [src['brazil']]),
        ('Latin America', 'The optics also mattered domestically because Brazilian exporters need confidence that the government can keep the US channel functional even if global trade blocs get rougher.', '<strong>Why it happened:</strong> diplomacy is being used as an economic stabiliser. If agribusiness and miners fear policy retaliation, investment plans stall quickly.', [src['brazil']]),
        ('Latin America', 'More broadly, the region is being sorted by who can keep commodity upside without getting trapped in great-power crossfire, and today’s Brazil-US signalling was part of that sorting process.', '<strong>Why it happened:</strong> trade fragmentation raises the premium on flexible partners. Countries that can stay commercially open while avoiding direct confrontation gain relative value.', [src['brazil']]),
    ],
    'Oceania': [
        ('Oceania', 'The delay to the Australia-Vanuatu security agreement mattered because Pacific states are showing they will monetise strategic urgency instead of simply yielding to it.', '<strong>Why it happened:</strong> smaller states gain leverage when larger powers feel they are running out of time. Delay is a bargaining tool, not necessarily a diplomatic failure.', [src['vanuatu']]),
        ('Oceania', 'The same story mattered economically because any longer period of shipping and fuel stress hits island import costs quickly, making security negotiations inseparable from logistics risk.', '<strong>Why it happened:</strong> geography amplifies freight shocks. In the Pacific, diplomacy and supply-chain resilience are now tightly linked.', [src['vanuatu'], src['airlines']]),
        ('Oceania', 'Australia’s regional posture is therefore getting more complicated, because allies want speed while partners want proof that security alignment will produce tangible benefits.', '<strong>Why it happened:</strong> pressure alone does not close deals. The benefits case has to outrun sovereignty anxiety, and today’s delay showed that threshold has not yet been met.', [src['vanuatu']]),
    ],
}

japan_ja = [
    ('🇯🇵 日本・政治/国債', '午後の日本で最も新しかった変化は、高市氏の圧勝が「成長期待」だけでなく「国債にもむしろ悪くない」と受け止められ始めたことだ。景気刺激があっても、財政運営は無秩序ではないと見る向きが増えたからだ。', '<strong>なぜそう読まれたか：</strong>市場は当初、減税がそのまま財政不安につながると警戒していた。だが大勝で政権運営が安定すると、政策実行がむしろ整理されるという見方が出てきた。', [src['japan_bonds'], src['japan_stocks']]),
    ('🇯🇵 日本・大引け', f'日経平均は{nikkei_level}（{nikkei_day}）で引けた。高市 mandate で内需株は買われた一方、円防衛が本格化すれば逆風になる輸出株は慎重に見られたからだ。', '<strong>なぜ割れたか：</strong>選挙の明確さは銀行、小売、国内景気株には追い風だった。しかし同じ明確さが円高方向の政策リスクも高め、輸出企業には一枚岩の追い風にならなかった。', [src['japan_stocks'], src['yen_jump']]),
    ('🇯🇵 日本・円防衛', f'USD/JPYが{usdjpy_level}（{usdjpy_day}）近辺で最大の注目点だったのは、円が単なる金利差の犠牲ではなく、東京が実際に管理しにいく市場だと見え始めたからだ。', '<strong>なぜ急に重くなったか：</strong>介入観測が効くのは、当局が本当に資金を使うと市場が信じる時だけだ。今回の急な円上昇は、投機筋がその可能性を一瞬でも本気で織り込んだ証拠だった。', [src['yen_jump'], src['japan_us']]),
    ('🇯🇵 日本・政策リスク', '高市氏の減税論は家計には魅力的でも、市場にとっては「本当に財源は大丈夫か」という午後の新しい論点を生んだ。', '<strong>なぜ論点化したか：</strong>圧勝後は公約実行への期待が上がる。だが債券投資家は人気より資金手当てを見るため、成長支援と財政自由の違いが急に重要になった。', [src['japan_taxcut'], src['japan_bonds']]),
    ('🇯🇵 日本・対米連携', '日本が米国との足並みを強調したことの重みが増したのは、円防衛が単独行動ではなく、対米戦略の一部に見えたほうが市場への効き目が増すからだ。', '<strong>なぜ外交が効くか：</strong>日本は金利差そのものをすぐ変えられない。だから外交で「この水準は試すと面倒だ」と思わせることが、為替政策の増幅装置になる。', [src['japan_us'], src['yen_jump']]),
    ('🇯🇵 日本・企業', 'LINE運営会社LYを巡るNaverの持分見直し観測が目立ったのは、データ、プラットフォーム、利用者接点をより国内に近い形で押さえたい空気が強まっているからだ。', '<strong>なぜ今この話か：</strong>地政学と規制が強まるほど、国境をまたぐ所有構造は中立ではなくなる。今回の議論は、日本が影響を及ぼしやすい所有体制を好み始めている流れの一部だ。', [src['line'], src['japan_us']]),
]

global_regions_ja = {
    '北米': [
        ('北米', f'米株はS&P 500が{spx_level}（{spx_day}）となったが、雇用の強さだけでは押し切れなかった。油高とイラン停戦の脆さが、景気の強さをそのまま安心材料にしなかったからだ。', '<strong>なぜ伸び切らないか：</strong>雇用が強いと景気後退懸念は下がるが、同時に利下げ期待も後退する。そこへ原油高が重なると、「良い成長」が「悪いインフレ」に変わりやすい。', [src['us_mixed'], src['truce_cracks']]),
        ('北米', 'ドルの勢いが少し鈍ったのは、強い米指標だけでは相場を説明しきれず、油と地政学が金融環境を締める方向にも効き始めたからだ。', '<strong>なぜ単純なドル高でないか：</strong>成長の強さが外部ショックで相殺されると、市場は米国一強のストーリーを弱める。今日はその切り替えが起きた。', [src['us_mixed'], src['truce_cracks']]),
        ('北米', '半導体主導の強さが目立ったのは、市場がマクロ全体には自信を持てない一方、AIなど一部の利益テーマだけはまだ信じているからだ。', '<strong>なぜ幅が狭いか：</strong>相場の主導役が限られる時は、投資家が広く景気に賭けるより、確度の高いテーマに逃げていることが多い。', [src['us_mixed']]),
    ],
    '欧州': [
        ('欧州', '欧州が最も関税の被害者に見えたのは、米国のEU車関税強化が輸出、雇用、政治の中心に近い産業を直撃するからだ。', '<strong>なぜ自動車が重いか：</strong>自動車関税は個別企業の問題で終わらず、工業景況感と成長期待に直結する。欧州では連鎖が速い。', [src['eu_tariffs']]),
        ('欧州', 'イラン停戦の信認が揺らぎ原油が再び上がったことも、内需の弱い欧州には特に痛かった。', '<strong>なぜ米国より痛いか：</strong>成長が弱いところに輸入インフレが来ると、家計と企業の両方に同時に効く。だから停戦のほころびだけで欧州株は重くなる。', [src['truce_cracks'], src['eu_tariffs']]),
        ('欧州', '午後の欧州は、単独の大事故がなくても「関税＋高エネルギー＋弱い工業」の三重苦で評価を下げられた。', '<strong>なぜ累積が重いか：</strong>中くらいのショックが複数重なる時に市場は最も冷たくなる。欧州はまさにその形だった。', [src['eu_tariffs'], src['truce_cracks']]),
    ],
    'アジア（日本除く）': [
        ('アジア（日本除く）', '中国の4月輸出反発は、中国がまだ世界需要の下支え役でいられる可能性を示した。', '<strong>なぜ強かったか：</strong>トランプ関連の通商リスク前に出荷を前倒ししたことや、主要市場向けの供給力がまだ生きていることが寄与したとみられる。', [src['china_exports']]),
        ('アジア（日本除く）', '一方でジミー・ライ氏への20年刑は、中国の政治リスクプレミアムが消えていないことを改めて示した。', '<strong>なぜ同時に重要か：</strong>輸出が良くても、法治と地政学の懸念が残れば評価倍率は伸びにくい。成長と政治リスクが同居している。', [src['jimmy_lai'], src['china_exports']]),
        ('アジア（日本除く）', 'インドの19億ドル信用保証は、油高が中小企業の資金繰りと雇用へ波及する前に止めたいという先回りだ。', '<strong>なぜ急ぐか：</strong>インドはエネルギー輸入国なので、原油高は輸送費と運転資金を通じて一気に広がる。政府はその連鎖を途中で断ちたい。', [src['india_credit'], src['airlines']]),
    ],
    '中東・アフリカ': [
        ('中東・アフリカ', f'WTIが{wti_level}（{wti_day}）近辺で高止まりしたのは、中東が単発ニュースではなく、持続的な供給リスクとして見られているからだ。', '<strong>なぜ下がりきらないか：</strong>市場は供給停止だけでなく、保険、迂回、在庫積み増しまで織り込む。停戦が脆ければそのコストは残る。', [src['truce_cracks'], src['airlines']]),
        ('中東・アフリカ', '航空会社の欠航が続くのは、航路安全、燃料費、運航確実性が同時に悪化したからだ。', '<strong>なぜ合理的対応か：</strong>どれか一つなら吸収できても、三つ同時は難しい。欠航は過剰反応ではなく採算防衛だ。', [src['airlines'], src['jetfuel']]),
        ('中東・アフリカ', 'ジェット燃料コスト上昇がマクロの話になるのは、旅行と物流を通じて物価や企業見通しへすぐ波及するからだ。', '<strong>なぜ世界が気にするか：</strong>航空コストはチケット、観光、貨物、出張に一気に効く。紛争が企業業績の問題に変わる最短経路の一つだ。', [src['jetfuel'], src['airlines']]),
    ],
    'ラテンアメリカ': [
        ('ラテンアメリカ', 'ルラ大統領がトランプとの関係改善を強調したのは、関税環境がさらに荒くなる前に米国との接点を確保したいからだ。', '<strong>なぜ今それが重要か：</strong>ブラジルは資源需要と外交柔軟性の両方を守りたい。米国との空気を悪くしないこと自体が政策資産になる。', [src['brazil']]),
        ('ラテンアメリカ', 'そのメッセージは国内経済向けでもある。輸出企業に、対米チャネルはまだ壊れていないと示す意味がある。', '<strong>なぜ安心材料か：</strong>外交安定は投資判断の前提になる。対外関係が読めないだけで企業は計画を遅らせやすい。', [src['brazil']]),
        ('ラテンアメリカ', '地域全体では、資源の追い風を取りつつ大国対立には巻き込まれにくい国ほど相対評価が上がりやすい。', '<strong>なぜそこが差になるか：</strong>分断が進むほど、柔軟な貿易相手の価値は高まる。今日のブラジルの動きはその文脈にある。', [src['brazil']]),
    ],
    'オセアニア': [
        ('オセアニア', '豪州とバヌアツの安保協定遅延は、太平洋の小国が戦略的な急ぎを自国の交渉力に変えていることを示した。', '<strong>なぜ遅延が意味を持つか：</strong>大国が急ぐほど、小国の価値は上がる。急がないこと自体が価格交渉になる。', [src['vanuatu']]),
        ('オセアニア', '同時に海運と燃料の不安が続くほど、島しょ国経済では安全保障と物流が切り離せなくなる。', '<strong>なぜ経済にも直結するか：</strong>距離の長い地域では運賃ショックがそのまま生活コストに跳ねる。外交は経済の話でもある。', [src['vanuatu'], src['airlines']]),
        ('オセアニア', '豪州の立場が難しいのは、同盟国は迅速さを求めるが、相手国は主権に見合う利益の可視化を求めるからだ。', '<strong>なぜまだ決まらないか：</strong>圧力だけでは協定は進まない。利益が不安を上回る必要がある。', [src['vanuatu']]),
    ],
}

market_sources = [src['japan_stocks'], src['yen_jump'], src['us_mixed'], src['truce_cracks'], src['yahoo']]

def build_body(lang='en'):
    if lang == 'en':
        japan_cards='\n'.join(story_card(x['tag'],x['headline'],x['body'],x['sources']) for x in japan)
        global_cards='\n'.join(story_card(tag,h,b,s) for items in global_regions.values() for tag,h,b,s in items)
        markets='\n'.join([
            table_card('EQUITIES','End-of-day equity snapshot',['Index','Level','Daily','Weekly','Monthly','YTD'],EQ_ROWS,'<strong>Why the larger moves happened:</strong> Japan outperformed on political clarity, the US tape was steadied by jobs and chips but capped by oil, and Europe stayed weaker because tariffs and imported energy hit a softer growth base. Any move above 2% should be read through policy repricing, oil-shock spillover, or both.',market_sources),
            table_card('FX & RATES','Currency and rate pressure points',['Instrument','Level','Daily','Weekly','Monthly','YTD'],FX_ROWS,'<strong>Why it matters:</strong> USD/JPY remains the fastest read on whether Tokyo’s afternoon confidence translates into sustained defence. Treasury yields and the dollar are no longer trading on jobs alone, they are also trading on whether oil keeps acting like a stealth tightening of financial conditions.',market_sources),
            table_card('COMMODITIES & CRYPTO','Commodity and digital-asset close',['Asset','Price','Daily','Weekly','Monthly','YTD'],CMD_ROWS,'<strong>Big mover logic:</strong> if crude moves more than 2%, the cleanest explanation is still truce fragility plus shipping and insurance stress. If silver or crypto move sharply, the more useful lens is changing dollar expectations and renewed inflation-hedge demand.',market_sources),
            f'''        <article class="card fade-in" data-image="{market_sources[0].get('image','')}"><span class="card-tag">HEALTH SCORE</span><h3 class="card-headline">{HEALTH}/100, a bit firmer than the morning because Japan gained policy clarity and China export data softened the global-growth scare, but still fragile because oil, aviation, and tariff risk remain live.</h3><p class="card-body"><strong>Why {HEALTH}:</strong> the afternoon improved because Tokyo looks more governable, the yen defence threat became more credible, and China’s export print offered some demand cushion. The score stays well below comfort because the same world still has a shaky truce, higher fuel stress, and Europe under tariff pressure.</p><div class="card-sources">\n{source_links(market_sources)}\n          </div></article>'''
        ])
        predictions = '''        <article class="card fade-in collapsible" data-image=""><span class="card-tag">TOMORROW</span><h3 class="card-headline">Watch whether the yen’s sudden jump gets followed by actual follow-through from Tokyo, because a one-off scare matters less than proof that officials will keep leaning if USD/JPY tests them again.</h3><div class="tap-hint">Tap to expand</div><p class="card-body"><strong>Why it matters:</strong> markets now believe intervention risk is real. The next step is to learn whether that belief changes positioning for more than a single session.</p><div class="card-sources">\n'''+source_links([src['yen_jump'],src['japan_us']])+'''\n          </div></article>
        <article class="card fade-in collapsible" data-image=""><span class="card-tag">WEEK AHEAD</span><h3 class="card-headline">The broader test is whether the oil-and-flight disruption story stays contained or starts cutting into earnings guidance, consumer travel, and inflation expectations across regions.</h3><div class="tap-hint">Tap to expand</div><p class="card-body"><strong>Why it matters:</strong> once higher fuel, insurance, and rerouting costs start showing up in company outlooks, volatility usually stops being headline-based and becomes structural.</p><div class="card-sources">\n'''+source_links([src['truce_cracks'],src['airlines'],src['jetfuel']])+'''\n          </div></article>'''
        bottom_line='The key change since morning is that <strong>Japan now looks like it has more policy agency than the rest of the macro tape.</strong> Takaichi’s win, a more believable yen defence posture, and a strategically important Line ownership shift all gave Tokyo fresh afternoon leverage. <strong>Bottom line:</strong> Japan improved on a relative basis, but the world is still being priced by oil, transport disruption, and tariff fragmentation.'
        sub=f'🇯🇵 The afternoon shift was real: Tokyo gained policy clarity, the yen suddenly had teeth, and Line ownership politics turned strategic, not just corporate · China added a demand cushion with stronger exports, but Hong Kong reminded markets that political risk still sits inside the Asia story · Globally, oil and flight disruption kept pressure on Europe and capped US upside · Health Score: {HEALTH}/100'
        footer='CEO Afternoon Briefing · Generated by Sanbot · Sunday, May 10, 2026'
        return f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html" class="active">EN</a><span class="sep">/</span><a href="ja.html">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">{WAR_DAY}</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_EN} — Afternoon Edition</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">Japan</a><a href="#global" class="nav-pill">Global</a><a href="#markets" class="nav-pill">Markets</a><a href="#predictions" class="nav-pill">Predictions</a><a href="#bottomline" class="nav-pill">Bottom Line</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">Japan Update — In Depth</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">Global — By Continent</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">Markets & Economy</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">Predictions</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''

    japan_cards='\n'.join(story_card(t,h,b,s,ja=True) for t,h,b,s in japan_ja)
    global_cards='\n'.join(story_card(tag,h,b,s,ja=True) for items in global_regions_ja.values() for tag,h,b,s in items)
    markets='\n'.join([
        table_card('株式','引け後マーケット一覧',['指数','水準','日次','週次','月次','年初来'],EQ_ROWS,'大きな値動きは、日本の政策明確化、米国の雇用と半導体の強さ、欧州の関税とエネルギー不安で説明できる。2%超の動きは、政策再評価か油ショック波及か、その両方で読むのが自然。',market_sources),
        table_card('為替・金利','通貨と金利の要点',['指標','水準','日次','週次','月次','年初来'],FX_ROWS,'USD/JPYは、東京の午後の自信が本物かどうかを映す最速指標。米金利とドルは、雇用だけでなく、油高が実質的な金融引き締めになるかどうかでも動いている。',market_sources),
        table_card('商品・暗号資産','商品とデジタル資産の引け',['資産','価格','日次','週次','月次','年初来'],CMD_ROWS,'原油の大きな動きは、停戦の脆さ、海運、保険コストで説明するのが最も自然。銀や暗号資産の大きな動きは、ドル観測とインフレヘッジ需要の変化で見るべきだ。',market_sources),
        f'''        <article class="card fade-in" data-image="{market_sources[0].get('image','')}"><span class="card-tag">ヘルススコア</span><h3 class="card-headline">{HEALTH}/100、朝より改善。理由は安心感ではなく、日本の政策視界が開け、中国輸出が需要不安を少し和らげたからだ。</h3><p class="card-body"><strong>なぜ{HEALTH}か：</strong>午後は東京の統治可能性が高まり、円防衛の信認も上がった。中国輸出も世界需要のクッションになった。一方で停戦の脆さ、燃料高、欧州関税リスクが残るので、快適圏には遠い。</p><div class="card-sources">\n{source_links(market_sources)}\n          </div></article>'''
    ])
    predictions='''        <article class="card fade-in collapsible" data-image=""><span class="card-tag">明日</span><h3 class="card-headline">円の急騰が一発の脅しで終わるのか、東京が実際に継続的な防衛姿勢を見せるのかを注視。</h3><div class="tap-hint">タップして展開</div><p class="card-body"><strong>なぜ重要か：</strong>介入リスクが本物だと市場が学び始めた。次はその学びが一日以上持つかどうかだ。</p><div class="card-sources">\n'''+source_links([src['yen_jump'],src['japan_us']])+'''\n          </div></article>
        <article class="card fade-in collapsible" data-image=""><span class="card-tag">今週</span><h3 class="card-headline">油とフライト混乱が相場の話で止まるのか、企業見通し、旅行需要、インフレ期待まで削り始めるのかが次の分岐点。</h3><div class="tap-hint">タップして展開</div><p class="card-body"><strong>なぜそこか：</strong>燃料、保険、迂回コストが企業ガイダンスに入り始めると、相場は見出し相場から構造相場へ変わる。</p><div class="card-sources">\n'''+source_links([src['truce_cracks'],src['airlines'],src['jetfuel']])+'''\n          </div></article>'''
    bottom_line='朝から変わった本質は、<strong>日本だけが相対的に政策の手数を増やし、世界はなお油と輸送と関税の計算に縛られている</strong>ことだ。高市氏の勝利、より信じられる円防衛、そしてLINEを巡る戦略的な所有問題が、東京に新しい午後の材料を与えた。<strong>結論：</strong>日本は相対改善したが、世界全体の値付けはまだ原油、輸送混乱、通商分断が支配している。'
    sub=f'🇯🇵 午後の変化は本物だった。東京は政策視界が開き、円に急に「歯」が生まれ、LINEの所有問題も戦略案件になった · 中国輸出は需要不安を和らげたが、香港は政治リスクが消えていないことを再確認させた · 世界では油高とフライト混乱が欧州を圧迫し、米株の上値も抑えた · Health Score: {HEALTH}/100'
    footer='CEO Afternoon Briefing · Generated by Sanbot · 2026年5月10日（日）'
    return f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html">EN</a><span class="sep">/</span><a href="ja.html" class="active">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">{WAR_DAY}</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_JA} 午後版</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">日本</a><a href="#global" class="nav-pill">世界</a><a href="#markets" class="nav-pill">市場</a><a href="#predictions" class="nav-pill">予測</a><a href="#bottomline" class="nav-pill">結論</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">日本アップデート</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">世界の動き</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">市場と経済</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">予測</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''

def build_page(path: Path, lang='en'):
    src_html = path.read_text()
    head = src_html.split('<body>')[0] + '<body>\n'
    head = re.sub(r'<title>CEO Briefing — [^<]+</title>', f'<title>CEO Briefing — {TITLE_DATE}</title>', head)
    path.write_text(head + build_body(lang))

build_page(BASE/'index.html','en')
build_page(BASE/'ja.html','ja')
print('updated')
