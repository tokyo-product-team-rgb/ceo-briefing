# -*- coding: utf-8 -*-
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BASE = Path('/Users/xand/.openclaw/workspace/ceo-briefing')
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TODAY_EN = 'Saturday, April 25, 2026'
TODAY_JA = '2026年4月25日（土）'
TITLE_DATE = 'Apr 25, 2026'


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


japan_sources = [
    gnews('Japan launches financial task force amid AI security fears Reuters'),
    gnews("Japan's core inflation stays below BOJ target, energy risks grow Reuters"),
    gnews('Japan to tap joint oil stockpiles, PM says, with no end seen to supply crisis Reuters'),
    gnews('Itochu, ERI to set up Japan venture to recycle electronics Reuters'),
    gnews('Toyota supplier Denso targets 11% return on equity by 2030 Reuters'),
    gnews('NextEra expects agreements on Japan-backed gas-fired data center projects within three months Reuters'),
    gnews("Japan's Nikkei rises as tech earnings overshadow Mideast concerns Reuters"),
]

japan = [
    {
        'tag': '🇯🇵 JAPAN · MARKET CLOSE',
        'headline': 'The Nikkei finished firmer after tech names absorbed most of the Middle East shock, because earnings and AI positioning outweighed oil anxiety into the close.',
        'body': '<strong>Why it happened:</strong> the afternoon tone improved because investors decided that strong semiconductor and platform earnings matter more for Japanese index heavyweights than one more round of geopolitical headlines. That causal chain matters: when traders believe profit momentum in Tokyo tech is still intact, they buy dips even with crude rising, which is why the market held up better than a pure energy-scare tape would suggest.',
        'sources': [japan_sources[6]],
    },
    {
        'tag': '🇯🇵 JAPAN · INFLATION / BOJ',
        'headline': 'Japan’s core inflation stayed below the BOJ target, even as energy pressure grew, because earlier price momentum cooled before the latest oil shock fully hit households.',
        'body': '<strong>Why it happened:</strong> Reuters framed the key tension clearly: underlying inflation was still soft enough to keep the BOJ cautious, but imported energy risk is rising again because the Iran-related oil shock is feeding straight into fuel and utility costs. In practice, that means the BOJ has less room to sound hawkish, which helps keep the yen soft and leaves Japan more exposed to the next round of imported inflation.',
        'sources': [japan_sources[1]],
    },
    {
        'tag': '🇯🇵 JAPAN · POLICY / AI',
        'headline': 'Tokyo launched a financial task force on AI security because regulators are worried powerful models could create operational and market-risk problems faster than banks can adapt.',
        'body': '<strong>Why it happened:</strong> this was not a generic innovation headline. The trigger was rising concern that frontier AI systems could affect fraud, cyber risk, model governance, and market stability all at once, pushing financial authorities to coordinate before a crisis forces them to. The deeper cause is that Japan does not want to repeat its usual pattern of regulating only after the technology is already embedded in critical infrastructure.',
        'sources': [japan_sources[0]],
    },
    {
        'tag': '🇯🇵 JAPAN · ENERGY SECURITY',
        'headline': 'Japan moved to tap joint oil stockpiles because Tokyo no longer believes the supply disruption will fade quickly on its own.',
        'body': '<strong>Why it happened:</strong> Reuters said the government acted because there is still no visible end to the supply crisis. The cause is straightforward but important: even without a total shutdown, prolonged friction around shipping, insurance, and routing keeps physical oil tight enough to threaten refiners and utilities. Releasing shared stocks is therefore less about panic and more about buying time while policymakers wait to see whether transport conditions normalize.',
        'sources': [japan_sources[2], gnews('Asian governments spend billions of dollars to offset oil price shock Reuters')],
    },
    {
        'tag': '🇯🇵 JAPAN · CORPORATE STRATEGY',
        'headline': 'Itochu and ERI agreed on a Japanese electronics-recycling venture because higher raw-material risk is making domestic circular supply chains more valuable.',
        'body': '<strong>Why it happened:</strong> the business logic is causation-heavy: when energy, shipping, and geopolitical risk make imported inputs less reliable, companies gain incentive to recover valuable materials at home. This is why the deal matters beyond ESG language. It reflects a broader Japanese corporate shift toward resilience, where waste recovery is increasingly treated as industrial policy rather than just environmental branding.',
        'sources': [japan_sources[3]],
    },
    {
        'tag': '🇯🇵 JAPAN · INDUSTRY / CAPEX',
        'headline': 'Denso’s new return-on-equity target underscored a tougher capital-discipline mood in Japan because investors are rewarding companies that prove they can convert scale into shareholder returns.',
        'body': '<strong>Why it happened:</strong> Japanese manufacturers are under pressure to show that governance reform is real, not cosmetic. By setting a harder profitability target now, Denso is responding to a market that has become much less tolerant of dormant balance sheets and subscale returns. The cause is the same one driving the broader Japan trade: foreign investors are willing to pay up, but only for companies that can justify better capital efficiency.',
        'sources': [japan_sources[4]],
    },
]

global_regions = {
    'North America': [
        ('North America', 'US stocks closed lower because hopes for a quick Iran deal faded and mixed earnings were not strong enough to cancel the fresh oil and risk-off pressure.', '<strong>Why it happened:</strong> Reuters said markets lost confidence in the idea that diplomacy would quickly bring down the geopolitical premium. Once that narrative weakened, traders stopped treating earnings as a free pass and started repricing the inflation and margin consequences of higher oil.', [gnews('Stocks close lower on fading hopes for quick Iran deal mixed quarterly earnings Reuters')]),
        ('North America', 'The dollar headed for a weekly gain because stalled US-Iran talks pushed investors back toward liquidity and safety.', '<strong>Why it happened:</strong> the causal chain is classic risk aversion: when geopolitical uncertainty rises and energy inflation risk stays alive, global money tends to rotate into dollars. That stronger dollar then tightens financial conditions for everyone else, which is why the FX move matters beyond the currency market itself.', [gnews('Dollar set for weekly gain on stalled US-Iran talks and Middle East uncertainty Reuters')]),
        ('North America', 'NextEra said Japan-backed gas-fired data-center projects are moving toward agreements because hyperscale power demand is rising faster than renewable build-outs can fully cover it.', '<strong>Why it happened:</strong> AI data-center load growth is forcing utilities and investors to prioritize reliable baseload capacity. The reason Japan-linked financing matters is that foreign capital still sees US power infrastructure as one of the cleanest ways to monetize the AI boom, even when fuel markets are volatile.', [japan_sources[5]]),
    ],
    'Europe': [
        ('Europe', 'The EU formally approved its Ukraine loan and a 20th Russia sanctions package because restored political unity became easier once energy logistics looked slightly more manageable.', '<strong>Why it happened:</strong> Brussels could move because member states judged the strategic cost of delay to be higher than the economic pain of another sanctions step. The deeper cause is that Europe wants to lock in support while markets are still functioning, not wait for a worse military or fiscal shock.', [gnews('EU formally approves Ukraine loan and 20th sanctions package against Russia Reuters')]),
        ('Europe', 'The US and EU prepared a preliminary critical-minerals partnership because both sides want more non-China supply security before the next industrial crunch hits.', '<strong>Why it happened:</strong> governments are reacting to the same lesson supply chains keep teaching them: if minerals stay concentrated, every battery, grid, and defense plan inherits that vulnerability. This deal is therefore about strategic redundancy, not just trade diplomacy.', [gnews('US EU to sign preliminary partnership deal on critical minerals on Friday Reuters')]),
        ('Europe', 'ECB watchers are focusing on fragility rather than victory because the oil shock is complicating the disinflation story just as growth is still soft.', '<strong>Why it happened:</strong> Reuters highlighted the central-bank dilemma. The cause is that energy can reaccelerate headline inflation without fixing weak demand, leaving the ECB stuck between protecting credibility and avoiding unnecessary growth damage.', [gnews('A fragile hold Five questions for the ECB Reuters')]),
    ],
    'Asia ex-Japan': [
        ('Asia ex-Japan', 'Asian shares turned jittery because US-Iran deadlock kept oil climbing and made investors question the morning risk rally.', '<strong>Why it happened:</strong> once traders realized there was no diplomatic breakthrough, the region had to reprice higher import bills and weaker sentiment at the same time. That is why the move was broad-based: oil is not just an energy story in Asia, it is a growth and inflation story too.', [gnews('Shares jittery oil advances on US-Iran deadlock Reuters')]),
        ('Asia ex-Japan', 'Honda will halt South Korea car sales because the company judged the market strain and competitive economics to be worse than the value of staying exposed.', '<strong>Why it happened:</strong> Reuters tied the move to broader pressure across Asian markets. The cause is that softer demand, pricing tension, and a tougher operating backdrop can make marginal geographies uneconomic, especially when companies are already reallocating capital toward EVs and core markets.', [gnews('Honda to halt South Korea car sales highlighting strain across Asian markets Reuters')]),
        ('Asia ex-Japan', 'Asian governments are spending billions to cushion the oil shock because leaders know fuel inflation can turn into social and political instability very quickly.', '<strong>Why it happened:</strong> subsidies and emergency support are rising because imported energy costs hit consumers before wages can catch up. The real cause is political risk management: governments would rather absorb fiscal pain now than face protest, weaker demand, and credibility damage later.', [gnews('Asian governments spend billions of dollars to offset oil price shock Reuters')]),
    ],
    'Middle East & Africa': [
        ('Middle East & Africa', 'Oil kept rising because traders still see escalating military tension and no credible path to a fast shipping normalization.', '<strong>Why it happened:</strong> the market is pricing not only possible supply loss, but also the practical drag from rerouting, insurance costs, and delayed cargoes. That is why crude can keep climbing even without a headline-grabbing outright closure.', [gnews('Oil rises on concerns over escalating military tensions in the Middle East Reuters')]),
        ('Middle East & Africa', 'Israel and Lebanon extended their ceasefire because both sides want to avoid adding another active front while Washington chases an Iran arrangement.', '<strong>Why it happened:</strong> the extension is about sequencing. The cause is not trust, but mutual incentive to keep one theatre from blowing up while larger regional bargaining is unresolved.', [gnews('Israel Lebanon extend ceasefire as Trump seeks best deal with Iran Reuters')]),
        ('Middle East & Africa', 'The broader war impact is seeping deeper into the economy because elevated fuel, freight, insurance, and security costs are now lasting long enough to hit corporate planning.', '<strong>Why it happened:</strong> once a shock persists, companies stop treating it as noise and start cutting guidance, delaying investment, and passing costs onward. That second-round effect is why the conflict matters so much more now than it did in the first few headline-driven days.', [gnews('Iran war impact seeps ever deeper into global economy Reuters')]),
    ],
    'Latin America': [
        ('Latin America', 'Mexico named economist Lazzeri as ambassador to Washington because Sheinbaum wants a more technically credible voice ahead of tougher trade and security negotiations.', '<strong>Why it happened:</strong> Reuters framed the choice as strategic. The cause is that Mexico expects a more transactional US relationship, so it is sending someone better suited to defend economic interests in a period where tariffs, migration, and industrial policy are all converging.', [gnews('Sheinbaum taps economist Lazzeri for Mexico ambassador to the US Reuters')]),
        ('Latin America', 'Bottler Arca’s stock jumped because volumes held up even after Mexico’s health tax, signaling demand was stronger than investors had feared.', '<strong>Why it happened:</strong> the share move came from a simple surprise: taxes were supposed to hurt consumption more visibly, but resilient volumes showed the pass-through and brand position were better than expected. That caused investors to re-rate the earnings risk lower.', [gnews('Bottler Arca stock jumps as volumes hold steady despite Mexican health tax Reuters')]),
        ('Latin America', 'El Salvador’s mass-trial spectacle showed Bukele is doubling down because his government sees public security theatrics as part of the political product, not a side effect.', '<strong>Why it happened:</strong> Reuters described prisoners watching their own trial on a big screen. The cause is that the administration wants to keep reinforcing its deterrence narrative domestically and internationally, even if that intensifies legal and human-rights criticism.', [gnews('In El Salvador shackled prisoners watch their mass trial on a big screen Reuters')]),
    ],
    'Oceania': [
        ('Oceania', 'Australia and Japan are preparing deeper economic-security ties because both governments want sturdier supply chains as the region becomes more strategically contested.', '<strong>Why it happened:</strong> the cause is shared vulnerability. Both countries are trying to reduce dependence on single suppliers in energy, minerals, and technology before the next disruption forces a more expensive response.', [gnews('Japan Australia eye joint declaration on economic security in May')]),
    ],
}

japan_ja = [
    ('🇯🇵 日本・大引け', '日経平均は午後に底堅く推移した。中東不安よりもハイテク決算とAI物色が勝ったからだ。', '<strong>なぜそうなったか：</strong>午後の相場は、原油高そのものよりも日本の大型テック株の利益成長が重視された。半導体やプラットフォーム関連の収益期待が残っている限り、投資家は地政学で下がった場面を押し目と見なしやすい。そのため、エネルギー懸念があっても日本株全体は崩れ切らなかった。', [japan_sources[6]]),
    ('🇯🇵 日本・物価/日銀', 'コアCPIは日銀目標を下回った一方、エネルギー由来の上振れリスクは強まった。', '<strong>なぜ重要か：</strong>基調インフレがまだ弱いので、日銀は急に強く引き締めへ動きにくい。しかし同時に、原油高が続けば家計向けの燃料・電力コストは押し上がる。この組み合わせが円安を長引かせ、後から輸入インフレを呼び込むという難しい因果関係になっている。', [japan_sources[1]]),
    ('🇯🇵 日本・AI政策', '金融庁まわりでAI安全保障のタスクフォースが立ち上がった。強力なモデルが金融システムに与えるリスクを先回りで抑えたいからだ。', '<strong>なぜ今か：</strong>不正、サイバー、モデル管理、市場混乱が同時に起こり得るとの懸念が強まっているため。日本は「普及してから規制する」後追いを避け、金融インフラにAIが深く入る前に枠組みを整えようとしている。', [japan_sources[0]]),
    ('🇯🇵 日本・エネルギー安全保障', '日本は共同備蓄の原油活用に動いた。供給不安がすぐには解けないと見ているからだ。', '<strong>なぜ放出か：</strong>海上輸送が完全停止しなくても、保険料、迂回、配船遅延が続けば実質的な供給逼迫になる。今回の動きはパニックではなく、物流正常化までの時間を買うための防御策と見た方が正確だ。', [japan_sources[2], gnews('Asian governments spend billions of dollars to offset oil price shock Reuters')]),
    ('🇯🇵 日本・企業戦略', '伊藤忠とERIは電子機器リサイクルの新会社を設立する。資源とサプライチェーンの不安定化で、国内循環の価値が上がっているからだ。', '<strong>なぜこの案件が効くか：</strong>原材料の輸入調達が不安定になるほど、国内で回収して再利用できる体制の価値は高まる。これは単なるESGではなく、資源安全保障と産業政策の一部として理解すべきニュース。', [japan_sources[3]]),
    ('🇯🇵 日本・資本効率', 'デンソーがROE目標を打ち出したのは、日本株投資家が規模より資本効率を重視し始めているからだ。', '<strong>なぜ出したか：</strong>コーポレートガバナンス改革が進む中で、余った資本を抱えるだけの企業は評価されにくくなった。海外投資家の日本買いが続く前提は「利益率と資本効率が改善すること」であり、今回の目標はその期待に応える動きだ。', [japan_sources[4]]),
]

global_regions_ja = {
    '北米': [
        ('北米', '米株は下落して引けた。イランを巡る早期妥結期待が後退し、決算だけでは原油高の不安を打ち消せなかったからだ。', '<strong>なぜ下げたか：</strong>地政学リスクが一時的なノイズではなく、再びインフレと利益率の問題として意識されたため。外交期待が弱まると、決算の強さだけでは相場全体を支えにくくなる。', [gnews('Stocks close lower on fading hopes for quick Iran deal mixed quarterly earnings Reuters')]),
        ('北米', 'ドルは週間で上昇方向。米イラン協議の停滞で、安全資産と流動性への需要が戻ったからだ。', '<strong>なぜドル高か：</strong>地政学不安とエネルギー高が残る局面では、投資家はまずドルへ逃げやすい。ドル高はそれ自体が世界の金融環境を引き締めるため、株や新興国にも波及する。', [gnews('Dollar set for weekly gain on stalled US-Iran talks and Middle East uncertainty Reuters')]),
        ('北米', 'NextEraの日本支援付きデータセンター向けガス火力案件は前進した。AI向け電力需要が再エネ増設の速度を上回っているからだ。', '<strong>なぜ進むか：</strong>データセンターは止められない電力を必要とするため、足元では安定供給が最優先になりやすい。AIブームを収益化する手段として、電力インフラに資金が集まり続けている。', [japan_sources[5]]),
    ],
    '欧州': [
        ('欧州', 'EUは対ウクライナ融資と第20弾対ロ制裁を正式承認した。先に支援枠を固める方が戦略的コストが低いと判断したからだ。', '<strong>なぜ今決めたか：</strong>後回しにすると軍事・財政の不確実性が増すため。エネルギー物流への警戒は残るが、それでも政治的には早く固定する方が合理的だとみられた。', [gnews('EU formally approves Ukraine loan and 20th sanctions package against Russia Reuters')]),
        ('欧州', '米欧は重要鉱物の暫定連携に署名へ。中国依存を減らさない限り、電池も送電網も防衛産業も脆弱なままだからだ。', '<strong>なぜ重要か：</strong>供給集中が残れば、次の産業ショックがそのまま政策ショックになる。今回は通商よりも、戦略的な冗長性づくりとして見るべき案件。', [gnews('US EU to sign preliminary partnership deal on critical minerals on Friday Reuters')]),
        ('欧州', 'ECBを巡る論点は「勝利」ではなく「もろさ」になっている。原油高がディスインフレを乱す一方で、景気はまだ弱いからだ。', '<strong>なぜ難しいか：</strong>エネルギーで見出しの物価が上がっても、需要まで強くなるわけではない。そのためECBは信認維持と景気悪化回避の間で難しい舵取りを迫られる。', [gnews('A fragile hold Five questions for the ECB Reuters')]),
    ],
    'アジア（日本除く）': [
        ('アジア（日本除く）', 'アジア株は神経質な動き。米イラン協議の行き詰まりで原油高が続き、朝のリスクオンが揺らいだからだ。', '<strong>なぜ広がったか：</strong>アジアにとって原油はエネルギー価格の問題であると同時に、成長率とインフレの問題でもある。外交進展が見えないと、輸入コスト上昇と景況感悪化を同時に織り込まざるを得ない。', [gnews('Shares jittery oil advances on US-Iran deadlock Reuters')]),
        ('アジア（日本除く）', 'ホンダは韓国での自動車販売を停止する。需要・価格競争・資本配分を考えると、残留メリットが薄れたからだ。', '<strong>なぜ撤退か：</strong>厳しい市場で収益性が落ちるほど、企業はEVや中核市場に資本を振り向ける。今回の判断は単発ではなく、アジア市場の選別強化の一例とみるべき。', [gnews('Honda to halt South Korea car sales highlighting strain across Asian markets Reuters')]),
        ('アジア（日本除く）', '各国政府は原油高対策に巨額支出を始めた。燃料インフレがすぐに社会不安へつながり得るからだ。', '<strong>なぜ補助金か：</strong>エネルギー価格は賃金より早く家計を直撃する。政府は財政負担を飲んででも、需要悪化と抗議リスクを先に抑えたい。', [gnews('Asian governments spend billions of dollars to offset oil price shock Reuters')]),
    ],
    '中東・アフリカ': [
        ('中東・アフリカ', '原油は上昇継続。軍事緊張が高止まりし、海上輸送の正常化がまだ見えないからだ。', '<strong>なぜ上がるか：</strong>市場は単なる供給量だけでなく、迂回、保険、遅延など実務面のコストも織り込み始めている。全面封鎖がなくても、物流摩擦だけで価格は十分押し上がる。', [gnews('Oil rises on concerns over escalating military tensions in the Middle East Reuters')]),
        ('中東・アフリカ', 'イスラエルとレバノンの停戦延長は、イラン交渉が片付くまで別戦線を広げたくないからだ。', '<strong>なぜ延長か：</strong>相互信頼よりも、今は戦線追加のコストが高いという計算が勝っている。地域全体の駆け引きが片付くまでの時間稼ぎに近い。', [gnews('Israel Lebanon extend ceasefire as Trump seeks best deal with Iran Reuters')]),
        ('中東・アフリカ', '戦争の経済的な傷はさらに深くなっている。燃料、保険、輸送の高コストが企業計画にまで入り始めたからだ。', '<strong>なぜフェーズが変わったか：</strong>ショックが長引くと、企業は一時要因ではなく恒常コストとして扱い始める。その瞬間に、投資延期や値上げ、業績下方修正が連鎖しやすくなる。', [gnews('Iran war impact seeps ever deeper into global economy Reuters')]),
    ],
    'ラテンアメリカ': [
        ('ラテンアメリカ', 'メキシコは対米大使にエコノミストを起用した。今後の対米交渉が通商・移民・産業政策を一体で扱う厳しい局面になるからだ。', '<strong>なぜこの人選か：</strong>よりテクニカルで経済交渉に強い人材を前面に出し、ワシントンでの防御力を高めたい意図がある。', [gnews('Sheinbaum taps economist Lazzeri for Mexico ambassador to the US Reuters')]),
        ('ラテンアメリカ', 'メキシコのボトラーArca株は上昇。健康税後も販売数量が想定ほど落ちなかったからだ。', '<strong>なぜ株高か：</strong>投資家が恐れていた需要悪化が限定的だと分かり、利益率への懸念が後退した。つまり価格転嫁とブランド力が市場予想より強かった。', [gnews('Bottler Arca stock jumps as volumes hold steady despite Mexican health tax Reuters')]),
        ('ラテンアメリカ', 'エルサルバドルの集団裁判演出は、ブケレ政権が治安強硬姿勢そのものを政治商品として維持したいからだ。', '<strong>なぜ続けるか：</strong>厳罰演出は国内支持を固める一方で、法的・人権上の批判も強める。しかし政権は後者より前者の政治的便益が大きいと見ている。', [gnews('In El Salvador shackled prisoners watch their mass trial on a big screen Reuters')]),
    ],
    'オセアニア': [
        ('オセアニア', '日本と豪州は経済安全保障の連携を深める方向。地域の供給網リスクが一段と戦略課題になっているからだ。', '<strong>なぜ近づくか：</strong>エネルギー、鉱物、技術のいずれも単一依存を減らす必要が高まっており、平時のうちに連携を固める方がコストが低いから。', [gnews('Japan Australia eye joint declaration on economic security in May')]),
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
    gnews('Shares jittery oil advances on US-Iran deadlock Reuters'),
    gnews('Dollar set for weekly gain on stalled US-Iran talks and Middle East uncertainty Reuters'),
    gnews('Oil rises on concerns over escalating military tensions in the Middle East Reuters'),
    {'url': 'https://finance.yahoo.com/', 'source': 'Yahoo Finance', 'title': 'Yahoo Finance', 'image': ''},
]


def build_body(lang='en'):
    if lang == 'en':
        japan_cards = '\n'.join(story_card(x['tag'], x['headline'], x['body'], x['sources']) for x in japan)
        global_cards = []
        for region, items in global_regions.items():
            for tag, headline, body, sources in items:
                global_cards.append(story_card(tag, headline, body, sources))
        global_cards = '\n'.join(global_cards)
        markets = '\n'.join([
            table_card('EQUITIES', 'End-of-day equity snapshot', ['Index', 'Level', 'Daily', 'Weekly', 'Monthly', 'YTD'], EQ_ROWS, '<strong>Why the bigger moves happened:</strong> if an equity move is large, the first question today is whether oil, the dollar, or earnings were in control. US indexes weakened because the Iran-deal optimism faded. Japan held up better because tech earnings and governance-friendly capital discipline still attract buyers. Any move above 2% should be read through that same chain: higher oil tightens margins, a firmer dollar tightens liquidity, and better earnings can offset only part of that pressure.', market_sources),
            table_card('FX & RATES', 'Currency and rate pressure points', ['Instrument', 'Level', 'Daily', 'Weekly', 'Monthly', 'YTD'], FX_ROWS, '<strong>Why it matters:</strong> the dollar stayed firm because markets still prefer liquidity while Iran talks stall. USD/JPY remains one of the cleanest pressure gauges for Japan, because a softer yen helps exporters but worsens the imported-energy problem. Treasury yields matter for the same reason: if oil keeps inflation sticky, rate cuts get harder.', market_sources),
            table_card('COMMODITIES & CRYPTO', 'Commodity and digital-asset close', ['Asset', 'Price', 'Daily', 'Weekly', 'Monthly', 'YTD'], CMD_ROWS, '<strong>Big mover logic:</strong> WTI is the most important swing variable because it transmits Middle East risk into freight, inflation, and margins. If silver or crypto move more than 2%, the most likely causes today are dollar strength, shifting inflation hedges, and changes in broad risk appetite rather than standalone sector news.', market_sources),
            '''        <article class="card fade-in" data-image="'''+(market_sources[0].get('image',''))+'''"><span class="card-tag">HEALTH SCORE</span><h3 class="card-headline">54/100, still investable, but less forgiving than the morning tape.</h3><p class="card-body"><strong>Why 54:</strong> Japan held together better than feared and governance-plus-tech is still a real support. But the afternoon global read turned less comfortable because US-Iran talks remained stuck, oil kept its premium, and the dollar strengthened again. That mix does not scream crisis, but it does mean the market is one bad shipping headline away from another risk-off leg.</p><div class="card-sources">\n'''+source_links(market_sources)+'''\n          </div></article>'''
        ])
        predictions = '''        <article class="card fade-in collapsible" data-image=""><span class="card-tag">TOMORROW</span><h3 class="card-headline">Watch whether Japan can still outperform if oil stays high and the yen stays soft.</h3><div class="tap-hint">Tap to expand</div><p class="card-body"><strong>Why it matters:</strong> Japan has handled the shock better than many peers because tech, governance reform, and foreign inflows are all real supports. The test is whether that remains true if imported-energy pressure keeps building faster than earnings optimism.</p></article>
        <article class="card fade-in collapsible" data-image=""><span class="card-tag">WEEK AHEAD</span><h3 class="card-headline">The key macro question is not the next headline, but whether oil and the dollar stay elevated long enough to damage demand.</h3><div class="tap-hint">Tap to expand</div><p class="card-body"><strong>Why it matters:</strong> if crude, freight, and the dollar remain high together, the impact broadens from markets into inflation, consumer spending, and policy hesitation. That is when a geopolitical shock stops being a market story and becomes an earnings story.</p></article>'''
        bottom_line = 'The afternoon told a cleaner story than the morning. <strong>Japan looked relatively strong not because risk disappeared, but because tech earnings, capital-discipline reform, and policy responsiveness still gave investors a reason to stay long.</strong> The rest of the world looked shakier because the US-Iran process is still stalled, oil is still expensive, and the dollar is tightening conditions again. <strong>Bottom line:</strong> this is still a tradable market, but the burden of proof has shifted back onto earnings and execution.'
        sub = '🇯🇵 Tokyo held up on tech earnings, while soft core inflation and higher energy risk kept the BOJ dilemma alive · Japan launched an AI financial-risk task force, tapped shared oil reserves, and saw more resilience-focused corporate moves from Itochu and Denso · Globally, stocks lost confidence in a quick Iran deal, oil stayed bid, the dollar firmed, and governments from Europe to Asia kept shifting toward security-first economic policy · Health Score: 54/100'
        footer = 'CEO Afternoon Briefing · Generated by Sanbot · Saturday, April 25, 2026'
        return f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html" class="active">EN</a><span class="sep">/</span><a href="ja.html">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">55</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_EN} — Afternoon Edition</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">Japan</a><a href="#global" class="nav-pill">Global</a><a href="#markets" class="nav-pill">Markets</a><a href="#predictions" class="nav-pill">Predictions</a><a href="#bottomline" class="nav-pill">Bottom Line</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">Japan Update — In Depth</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">Global — By Continent</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">Markets & Economy</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">Predictions</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Kyodo, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''

    japan_cards = '\n'.join(story_card(t, h, b, s, ja=True) for t, h, b, s in japan_ja)
    global_cards = []
    for region, items in global_regions_ja.items():
        for tag, headline, body, sources in items:
            global_cards.append(story_card(tag, headline, body, sources, ja=True))
    global_cards = '\n'.join(global_cards)
    markets = '\n'.join([
        table_card('株式', '引け後マーケット一覧', ['指数', '水準', '日次', '週次', '月次', '年初来'], EQ_ROWS, '<strong>大きな値動きの因果：</strong>今日は「原油」「ドル」「決算」のどれが主因かで読むのが正しい。米株はイラン協議期待の後退で重く、日本株はテック収益と資本効率期待で相対的に耐えた。2%超の大きな動きは、多くがこの3要因の組み合わせで説明できる。', market_sources),
        table_card('為替・金利', '通貨と金利の要点', ['指標', '水準', '日次', '週次', '月次', '年初来'], FX_ROWS, '<strong>なぜ重要か：</strong>ドル高は、イラン協議停滞で投資家が流動性を優先しているサイン。USD/JPYは日本にとって特に重要で、円安は輸出株を助ける一方、輸入エネルギー負担を悪化させる。', market_sources),
        table_card('商品・暗号資産', '商品とデジタル資産の引け', ['資産', '価格', '日次', '週次', '月次', '年初来'], CMD_ROWS, '<strong>大きく動く理由：</strong>WTIは中東リスクを運賃、インフレ、企業マージンへ伝える最重要変数。銀や暗号資産が2%以上動く場合も、今日はドル高、インフレヘッジの見直し、全体リスク許容度の変化で読むのが自然。', market_sources),
        '''        <article class="card fade-in" data-image="'''+(market_sources[0].get('image',''))+'''"><span class="card-tag">ヘルススコア</span><h3 class="card-headline">54/100、まだ投資可能だが、朝より相場は厳しくなった。</h3><p class="card-body"><strong>なぜ54か：</strong>日本は想定より強く、テックとガバナンス改革が支えになっている。ただし世界全体では米イラン協議が進まず、原油高とドル高が残った。つまり危機ではないが、海上輸送や原油の悪化ヘッドライン1本で再びリスクオフに傾きやすい状態だ。</p><div class="card-sources">\n'''+source_links(market_sources)+'''\n          </div></article>'''
    ])
    predictions = '''        <article class="card fade-in collapsible" data-image=""><span class="card-tag">明日</span><h3 class="card-headline">原油高と円安が続いても、日本株が相対優位を保てるかが焦点。</h3><div class="tap-hint">タップして展開</div><p class="card-body"><strong>なぜ注目か：</strong>日本株はテック、資本効率改善、海外資金流入に支えられている。ただし輸入エネルギー負担の増加が業績期待を上回れば、強さは試される。</p></article>
    <article class="card fade-in collapsible" data-image=""><span class="card-tag">来週</span><h3 class="card-headline">重要なのは次の見出しではなく、高い原油とドルが需要を傷めるほど長引くかどうか。</h3><div class="tap-hint">タップして展開</div><p class="card-body"><strong>なぜそこか：</strong>原油、運賃、ドル高が同時に長引くと、市場の話ではなく家計・需要・政策の話になる。その瞬間に地政学ショックは本格的な業績リスクへ変わる。</p></article>'''
    bottom_line = '午後の相場が教えたのは、<strong>日本の強さは「安全」だからではなく、買う理由がまだ残っているから</strong>ということだ。テック収益、資本効率改革、政策の先回り対応は日本の支えになった。一方で世界では、イラン協議停滞、原油高、ドル高が再び重しになった。<strong>結論：</strong>まだ崩壊ではないが、相場の主導権は再び「期待」ではなく「実行力」に戻っている。'
    sub = '🇯🇵 日本株はテック決算で底堅く、コア物価の弱さとエネルギー高で日銀の難しさが続いた · AI金融リスクの新タスクフォース、共同石油備蓄の活用、伊藤忠とデンソーの動きは「安全保障と資本効率」が日本の午後テーマだったことを示した · 世界ではイラン協議停滞で原油とドルが高止まりし、各地域がより防衛的な経済運営へ傾いた · Health Score: 54/100'
    footer = 'CEO Afternoon Briefing · Generated by Sanbot · 2026年4月25日（土）'
    return f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html">EN</a><span class="sep">/</span><a href="ja.html" class="active">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">55</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_JA} 午後版</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">日本</a><a href="#global" class="nav-pill">世界</a><a href="#markets" class="nav-pill">市場</a><a href="#predictions" class="nav-pill">予測</a><a href="#bottomline" class="nav-pill">結論</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">日本アップデート</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">世界の動き</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">市場と経済</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">予測</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Kyodo, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''


def build_page(path: Path, lang='en'):
    src = path.read_text()
    head = src.split('<body>')[0] + '<body>\n'
    body = build_body(lang)
    page = re.sub(r'<title>CEO Briefing — [^<]+</title>', f'<title>CEO Briefing — {TITLE_DATE}</title>', head) + body
    path.write_text(page)


build_page(BASE / 'index.html', 'en')
build_page(BASE / 'ja.html', 'ja')
print('updated')
