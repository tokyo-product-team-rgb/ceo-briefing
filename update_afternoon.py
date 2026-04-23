# -*- coding: utf-8 -*-
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = Path('/Users/xand/.openclaw/workspace/ceo-briefing')
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TODAY_EN = 'Thursday, April 23, 2026'
TODAY_JA = '2026年4月23日（木）'
TITLE_DATE = 'Apr 23, 2026'


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


def story_card(tag, headline, body, sources, ja=False):
    tap = 'タップして展開' if ja else 'Tap to expand'
    return f'''        <article class="card featured fade-in collapsible" data-image="{sources[0].get('image','') if sources else ''}">
          <span class="card-tag{' japan' if '🇯🇵' in tag or '日本' in tag else ''}">{tag}</span>
          <h3 class="card-headline">{headline}</h3>
          <div class="tap-hint">{tap}</div>
          <p class="card-body">{body}</p>
          <div class="card-sources">\n{source_links(sources)}\n          </div>
        </article>'''


japan = [
    {
        'tag': '🇯🇵 JAPAN · MARKET CLOSE',
        'headline': 'Nikkei finished near 59,100 after failing to hold 60,000, because afternoon profit-taking offset the morning AI and relief bid.',
        'body': '<strong>Why it happened:</strong> Reuters said the Nikkei briefly cleared 60,000 but then reversed as traders locked in gains after a huge run. That pullback matters because the cause was not a fresh macro shock, it was positioning: investors who had chased the AI rally and ceasefire optimism took money off the table once the index hit a psychological milestone. Even so, the close stayed elevated because foreign money is still rotating into Japan on the view that earnings can tolerate a weak yen better than Europe or China can tolerate higher energy costs.',
        'sources': [gnews('Japan Nikkei reverses below 60000 level as profit-taking steps in Reuters'), gnews('Foreign investors buy Japan stocks on US-Iran peace hopes AI rally Reuters')],
    },
    {
        'tag': '🇯🇵 JAPAN · BOJ / FX',
        'headline': 'The yen stayed weak around ¥159 per dollar because the BOJ is expected to keep rates steady and soften its hawkish tone despite imported inflation risks.',
        'body': '<strong>Why it happened:</strong> Reuters reported the Bank of Japan is widely expected to keep policy unchanged while dialing back hawkish guidance. That causal chain is straightforward: if the BOJ does not validate near-term tightening bets, rate differentials stay wide, macro funds keep buying dollars, and the yen remains too weak to cushion Japan from higher imported fuel costs. The afternoon market read was that equities can live with that trade-off for now, but households and importers cannot.',
        'sources': [gnews('Bank of Japan seen dropping hawkish signs even as it keeps rates steady Reuters'), gnews('Nikkei yen Reuters when:1d')],
    },
    {
        'tag': '🇯🇵 JAPAN · REAL ECONOMY',
        'headline': 'Japan’s factory activity expanded at the strongest pace in four years because chip demand and domestic output recovered faster than the energy shock hit order books.',
        'body': '<strong>Why it happened:</strong> the PMI rebound reflects real demand in electronics and machinery, not just financial-market optimism. That matters this afternoon because it explains why investors were still willing to buy cyclical names even after the Nikkei slipped from its intraday high. In other words, profit-taking hit the index level, but the underlying cause for optimism remains a stronger manufacturing pipeline than the market feared this morning.',
        'sources': [gnews('Japan factory activity expands at strongest pace in 4 years PMI shows Reuters')],
    },
    {
        'tag': '🇯🇵 JAPAN · CORPORATE FINANCE',
        'headline': 'SoftBank’s reported push for a $10 billion margin loan backed by OpenAI shares shows Japanese capital is still leaning into AI risk because financing markets think the theme can outrun war-driven volatility.',
        'body': '<strong>Why it happened:</strong> Reuters said SoftBank is seeking financing against one of the market’s highest-conviction assets. The cause is twofold: AI remains one of the few sectors where lenders still believe earnings optionality is widening, and Japanese financial conditions are loose enough that large borrowers can still structure aggressive trades. The afternoon takeaway is that Japan’s corporate story was not only about macro and the yen, it was also about balance sheets still being willing to fund long-duration tech exposure.',
        'sources': [gnews('SoftBank seeks 10 billion margin loan backed by OpenAI shares Reuters')],
    },
    {
        'tag': '🇯🇵 JAPAN · TRADE POLICY',
        'headline': 'Tokyo moved to press the EU over local-content EV rules because Japan fears a bloc-made preference would lock its automakers out just as Europe’s EV demand is recovering.',
        'body': '<strong>Why it happened:</strong> Kyodo reported Japan plans to urge the EU to revise a proposal favoring Europe-made EVs. The cause is strategic, not symbolic: Japanese automakers are already absorbing higher logistics and battery costs, so a discriminatory rule in Europe would hit them at the exact moment the region is becoming a more important source of demand. Tokyo’s push today was about defending export access before the rulebook hardens.',
        'sources': [gnews('Japan plans to urge EU to revise proposed policy favoring bloc-made EVs Kyodo')],
    },
    {
        'tag': '🇯🇵 JAPAN · ENERGY SECURITY',
        'headline': 'Japan and Saudi Arabia agreed to work on alternative oil transport routes because Tokyo is trying to reduce single-point dependence on Hormuz after the latest disruption scare.',
        'body': '<strong>Why it happened:</strong> Kyodo said the two countries agreed to cooperate on alternative routing. The cause is obvious but important: policymakers now understand that even a nominally reopened strait can stay commercially impaired if insurance, minesweeping, convoying, and tanker scheduling remain disrupted. Japan is therefore shifting from reactive reserve management toward structural redundancy, because the country cannot let every Middle East headline become a yen and equity event.',
        'sources': [gnews('Japan Saudi Arabia agree to cooperate on alternative oil transport route Kyodo')],
    },
]

global_regions = {
    'North America': [
        ('NORTH AMERICA', 'The S&P 500 and Nasdaq closed at records because investors extended the Iran ceasefire narrative just long enough for earnings to dominate the tape.', '<strong>Why it happened:</strong> Reuters said US equities hit records on the back of earnings and an extension of the ceasefire story. The cause was not that geopolitical risk disappeared, it was that investors temporarily believed the worst oil scenario had been deferred, which let strong corporate results carry the index higher before today’s fresh Hormuz doubts resurfaced.', [gnews('S&P Nasdaq close at records on Iran ceasefire extension earnings Reuters')]),
        ('NORTH AMERICA', 'Oil kept rising in US trading because talks with Iran made no real progress and Hormuz shipping stayed disrupted.', '<strong>Why it happened:</strong> Reuters framed the move around a simple causal chain: no diplomatic breakthrough means no quick normalization in freight, insurance, or tanker traffic, so crude keeps rebuilding a risk premium. That matters for North America because higher oil supports energy names but reintroduces inflation pressure into the broader US rate outlook.', [gnews('Oil gains on lack of progress on US-Iran talks Hormuz shipping still disrupted Reuters')]),
        ('NORTH AMERICA', 'The US Senate moved toward advancing more ICE and border funding because election-year politics are pulling security spending back to the center of the agenda.', '<strong>Why it happened:</strong> Reuters reported the bill advanced as lawmakers responded to border politics and pressure to show operational control. The cause is domestic political competition: both parties see migration and enforcement as high-salience voter issues, so funding momentum rises when leadership thinks the issue can shape the next campaign cycle.', [gnews('US Senate edges toward advancing ICE border funding plan Reuters')]),
    ],
    'Europe': [
        ('EUROPE', 'European rooftop solar demand jumped because the Iran-linked energy shock pushed households to cut their exposure to grid and fuel bills.', '<strong>Why it happened:</strong> Reuters said the war revived solar demand. The cause is direct household economics: when oil and gas uncertainty lifts expected energy bills, payback periods on rooftop systems compress, so adoption accelerates without needing a new subsidy round.', [gnews('Iran war revives European rooftop solar demand to cut energy bills Reuters')]),
        ('EUROPE', 'European car sales grew in March because EV demand more than offset combustion-engine weakness.', '<strong>Why it happened:</strong> Reuters reported EV growth carried the market higher. The cause is that higher fuel costs and tighter emissions policy are finally pulling in the same direction, making electric models more attractive just as legacy combustion sales lose pricing power.', [gnews('European car sales grow in March as EV rise offsets combustion engine decline Reuters')]),
        ('EUROPE', 'The EU kept preparing its €90 billion Ukraine loan package because restored Druzhba flows reduced one of the immediate financing obstacles.', '<strong>Why it happened:</strong> Reuters explained that Russian oil flows through Druzhba restarted, unblocking the mechanics around the loan plan. The causal chain is that restored pipeline operation eased near-term energy-management pressure, which gave Brussels more room to finalize financing and sanctions sequencing.', [gnews('Explainer How will the EU 90 billion euro loan to Ukraine work Reuters'), gnews('Druzhba pipeline restarts Russian oil flows to Europe unblocking EU loan for Kyiv Reuters')]),
    ],
    'Asia ex-Japan': [
        ('ASIA EX-JAPAN', 'South Korea’s Q1 growth beat forecasts because AI-driven chip demand remained strong enough to overpower external uncertainty.', '<strong>Why it happened:</strong> Reuters-linked coverage said the economy outperformed thanks to semiconductors. The cause is concentrated but real: memory and AI infrastructure demand are still expanding so fast that they are lifting exports, capex, and inventory rebuilding even while the broader region remains exposed to oil risk.', [gnews('South Korea economic growth roared past estimates in Q1 thanks to chips Reuters')]),
        ('ASIA EX-JAPAN', 'Samsung union workers planned another rally because labor believes chip profits and record stock performance justify a tougher wage push.', '<strong>Why it happened:</strong> Reuters reported labor unrest is growing. The cause is classic bargaining leverage: when workers see a company benefiting from a strong cycle, they press harder for pay and working-condition concessions before management can argue the boom has faded.', [gnews('Unionised Samsung workers to hold rally in South Korea as labour unrest grows Reuters')]),
        ('ASIA EX-JAPAN', 'China faced fresh criticism over pressure on African states to block Taiwan’s president because Beijing is trying to narrow Taipei’s diplomatic room before any high-visibility trip can happen.', '<strong>Why it happened:</strong> Reuters said the US criticized China’s pressure campaign. The cause is preemption: Beijing treats transit diplomacy as legitimacy signaling, so it tries to stop symbolic visits before they turn into broader recognition or security cooperation.', [gnews('US criticizes China pressure on African countries to block Taiwan president trip Reuters')]),
    ],
    'Middle East & Africa': [
        ('MIDDLE EAST & AFRICA', 'Iran tightened control of Hormuz after the US called off renewed attacks, because Tehran wants leverage from the ceasefire without surrendering its maritime pressure point.', '<strong>Why it happened:</strong> Reuters reported Iran kept tightening its grip even after the immediate strike risk fell. The cause is bargaining power: by controlling shipping friction short of a total closure, Tehran can keep economic pressure alive while still leaving room for diplomacy.', [gnews('Iran tightens control of Hormuz after US calls off renewed attacks Reuters')]),
        ('MIDDLE EAST & AFRICA', 'Saudi Arabia and the Philippines will join JPMorgan’s emerging-market bond index in 2027 because benchmark providers are rewarding larger, more liquid local-currency markets.', '<strong>Why it happened:</strong> Reuters said both will enter the index next year. The cause is structural index inclusion logic: once liquidity, accessibility, and market size cross a threshold, passive inflows become more likely, which is why the announcement matters well before actual inclusion day.', [gnews('Saudi Arabia Philippines to join JPMorgan emerging market bond index in 2027 Reuters')]),
        ('MIDDLE EAST & AFRICA', 'Companies from paint makers to airlines darkened their outlooks because war-driven fuel and shipping costs are now feeding directly into margins.', '<strong>Why it happened:</strong> Reuters highlighted rising costs across sectors. The cause is second-round transmission: once oil and freight volatility persist long enough, they move from market headlines into corporate guidance, where they hit pricing, inventory planning, and consumer demand at the same time.', [gnews('From paint to flights Iran war lifts costs darkens outlooks Reuters')]),
    ],
    'Latin America': [
        ('LATIN AMERICA', 'Mexico said it should not be nostalgic for zero tariffs because officials expect the next USMCA review to be more transactional and defensive.', '<strong>Why it happened:</strong> Reuters quoted Mexico’s economy minister signaling a tougher reality. The cause is political: Washington’s trade posture is shifting toward strategic leverage, so Mexico is preparing businesses for a review shaped less by free-trade ideology and more by supply-chain bargaining.', [gnews('Mexico shouldnt be nostalgic about zero tariff era economy minister says Reuters')]),
        ('LATIN AMERICA', 'Mexico reopened the Teotihuacan pyramids under heavy police presence because authorities wanted to restore tourism revenue without appearing soft after the deadly shooting.', '<strong>Why it happened:</strong> Reuters reported the site reopened with visible security. The cause is a trade-off between economic continuity and public confidence: the government needs visitors back, but only if it can show the response is strong enough to contain reputational damage.', [gnews('Mexico reopens famed pyramids under heavy police presence after deadly shooting Reuters')]),
        ('LATIN AMERICA', 'Banorte is pushing cashless payments at Azteca ahead of the World Cup because event-driven infrastructure deadlines are accelerating Mexico’s payments modernization.', '<strong>Why it happened:</strong> Reuters said the bank is expanding digital payments at the stadium. The cause is timing pressure: mega-events force operators to upgrade throughput, security, and data capture faster than they otherwise would, which makes sport a trigger for fintech rollout.', [gnews('Banorte pushes cashless payments at Azteca as World Cup deadline nears Reuters')]),
    ],
    'Oceania': [
        ('OCEANIA', 'New Zealand said the oil shock delays recovery but does not derail it because domestic demand is stabilizing even as imported energy costs bite.', '<strong>Why it happened:</strong> Reuters quoted the finance minister saying recovery is delayed rather than broken. The cause is that the economy entered the shock with some cyclical healing already underway, so higher fuel costs are slowing momentum, not fully reversing it, unless the external energy hit lasts much longer.', [gnews('New Zealand economic recovery delayed but not derailed finance minister says Reuters')]),
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
    gnews('Oil gains on lack of progress on US-Iran talks Hormuz shipping still disrupted Reuters'),
    gnews('S&P Nasdaq close at records on Iran ceasefire extension earnings Reuters'),
    {'url': 'https://finance.yahoo.com/', 'source': 'Yahoo Finance', 'title': 'Yahoo Finance', 'image': ''},
]


def build_index(lang='en'):
    src = (BASE / ('index.html' if lang == 'en' else 'ja.html')).read_text()
    head = src.split('<body>')[0] + '<body>\n'

    if lang == 'en':
        japan_cards = '\n'.join(story_card(x['tag'], x['headline'], x['body'], x['sources']) for x in japan)
        global_cards = []
        for region, items in global_regions.items():
            for tag, headline, body, sources in items:
                global_cards.append(story_card(region, headline, body, sources))
        global_cards = '\n'.join(global_cards)
        markets = '\n'.join([
            table_card('EQUITIES', 'End-of-day equity snapshot', ['Index', 'Level', 'Daily', 'Weekly', 'Monthly', 'YTD'], EQ_ROWS, '<strong>Why the notable moves happened:</strong> the Nikkei stayed elevated because foreign inflows and a weak yen still support exporters, but it gave back intraday gains after hitting 60,000 because traders took profits. The S&P and Nasdaq held record territory because earnings temporarily outweighed geopolitics. Brazil lagged because higher global energy costs and tighter financial conditions are a harder mix for Latin risk assets.', market_sources),
            table_card('FX & RATES', 'Currency and rate pressure points', ['Instrument', 'Level', 'Daily', 'Weekly', 'Monthly', 'YTD'], FX_ROWS, '<strong>Why it matters:</strong> USD/JPY near 159 is the cleanest signal that Japan still has not solved the imported-inflation problem. A firm dollar and steady US yields tell you investors still prefer liquidity over declaring the crisis over.', market_sources),
            table_card('COMMODITIES & CRYPTO', 'Commodity and digital-asset close', ['Asset', 'Price', 'Daily', 'Weekly', 'Monthly', 'YTD'], CMD_ROWS, '<strong>Big mover logic:</strong> silver fell more than 2% because the stronger dollar and cooling inflation hedges outweighed safe-haven buying. WTI rose because the market still sees disrupted Hormuz logistics, not a true normalization. Bitcoin rose because risk appetite did not fully unwind after Wall Street records, but crypto stayed secondary to oil and FX headlines.', market_sources),
            '''        <article class="card fade-in" data-image="">
          <span class="card-tag">HEALTH SCORE</span>
          <h3 class="card-headline">58/100, resilient but still headline-fragile.</h3>
          <p class="card-body"><strong>Why 58:</strong> markets are healthier than this morning because US stocks kept their record close, Japan still held most of its gains, and South Korea’s chip-led growth print reassured Asia. But the score stops below 60 because Hormuz friction is still lifting oil, the dollar remains firm, and the BOJ is not giving Japan a currency shock absorber. That means every geopolitical flare-up can still travel quickly into fuel, freight, FX, and equity sentiment.</p>
          <div class="card-sources">\n''' + source_links(market_sources) + '''\n          </div>
        </article>'''
        ])
        predictions = '''        <article class="card fade-in collapsible" data-image="">
          <span class="card-tag">TOMORROW</span>
          <h3 class="card-headline">Watch whether Japan can hold the bid if the yen weakens further.</h3>
          <div class="tap-hint">Tap to expand</div>
          <p class="card-body"><strong>Why it matters:</strong> a softer yen helps exporters until the market decides imported energy pain is overtaking earnings support. If USD/JPY pushes further higher without a BOJ pushback, tomorrow’s question is whether the Nikkei can keep rising on foreign inflows alone.</p>
        </article>
        <article class="card fade-in collapsible" data-image="">
          <span class="card-tag">WEEK AHEAD</span>
          <h3 class="card-headline">The bigger test is whether shipping conditions improve, not whether ceasefire headlines survive.</h3>
          <div class="tap-hint">Tap to expand</div>
          <p class="card-body"><strong>Why it matters:</strong> if tanker traffic, insurance pricing, and route security do not normalize, higher oil will keep feeding inflation, consumer caution, and policy hesitation. That would cap Japan’s upside even if AI and chip demand stay strong.</p>
        </article>'''
        bottom_line = 'Today\'s afternoon move was a classic reminder that <strong>price action is about causation, not headlines</strong>. Japan held up because foreign investors still like a weak-yen, AI-friendly market and the factory data gave them a real-economy reason to stay. But the country is still vulnerable because the same BOJ caution that flatters stocks leaves the yen too weak to absorb energy shocks. Globally, Wall Street stayed strong because earnings bought time, while oil kept rising because shipping reality never fully matched the ceasefire story. <strong>Bottom line:</strong> the afternoon was better than the morning, but it was not safer.'
        sub = '🇯🇵 Nikkei held near 59,100 after profit-taking knocked it back below 60,000, while the yen stayed weak near ¥159 because the BOJ is expected to hold steady and sound less hawkish · SoftBank chased AI financing, Tokyo pushed back on EU EV rules, and Japan-Saudi energy-route talks underscored how seriously supply security is now being treated · Wall Street closed at records on earnings, South Korea beat on chips, Europe saw EV and rooftop-solar demand rise on fuel-cost pressure, and oil kept rebuilding risk premium because Hormuz shipping remains impaired · Health Score: 58/100'
        footer = 'CEO Afternoon Briefing · Generated by Sanbot · Thursday, April 23, 2026'
        body = f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html" class="active">EN</a><span class="sep">/</span><a href="ja.html">JA</a></div><div class="masthead-inner"><div class="overline">AFTERNOON INTELLIGENCE BRIEF</div><div class="war-day-counter" id="war-day-badge">🔴 IRAN WAR — DAY <span class="day-num" id="war-day-num">54</span></div><br><div class="econ-countdown" id="econ-countdown">⏱ ECONOMIC DAMAGE WINDOW: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO Afternoon Briefing</h1><div class="edition-date">{TODAY_EN} — Afternoon Edition</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">Japan</a><a href="#global" class="nav-pill">Global</a><a href="#markets" class="nav-pill">Markets</a><a href="#predictions" class="nav-pill">Predictions</a><a href="#bottomline" class="nav-pill">Bottom Line</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">Japan Update — In Depth</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">Global — By Continent</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">Markets & Economy</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">Predictions</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 Bottom Line</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>Data sources: Reuters, Kyodo, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));const needle=document.getElementById('gauge-needle');if(needle){{const score=58;const rotation=-90+(score/100)*180;setTimeout(()=>{{needle.style.transform=`rotate(${{rotation}}deg)`;}},300);}}</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ ECONOMIC DAMAGE WINDOW IN <span class="countdown-num">'+daysLeft+'</span> DAYS';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 ECONOMIC DAMAGE WINDOW — <span class="countdown-num" style="color:#fff;">NOW</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ OIL ELEVATED '+weeksPast+' WEEKS — PAST DAMAGE THRESHOLD';}}}})();</script><script src='audio-player.js'></script></body></html>'''
    else:
        japan_ja = [
            ('🇯🇵 日本・大引け', '日経平均は60,000円を維持できず59,100円近辺で終了。午後に利益確定売りが出たが、高値圏は保った。', '<strong>なぜそうなったか：</strong>ロイターによると、60,000円突破は達成感を呼び、AI相場と停戦期待で積み上がったポジションに利益確定が出た。ただし下げ切らなかったのは、海外勢が「円安でも業績が持つ日本株」をまだ選好しているから。つまり下落の原因は新たな悪材料ではなく、過熱後の利食いだった。', japan[0]['sources']),
            ('🇯🇵 日本・日銀/為替', '円は1ドル159円前後で弱いまま。日銀が据え置きかつややハト派寄りと見られている。', '<strong>なぜ円安か：</strong>日銀が早期追加利上げを示唆しない限り、金利差を材料にしたドル買いが続くから。円が弱いと輸出株には追い風だが、輸入燃料コストには逆風で、日本経済には両面の影響が残る。', japan[1]['sources']),
            ('🇯🇵 日本・景況感', '製造業PMIは4年ぶりの強い伸び。半導体と機械需要が午後の日本株の安心材料になった。', '<strong>なぜ強いか：</strong>実需のある電子部品、機械、在庫積み増しが効いているため。指数全体は利食いで押されたが、午後に景気敏感株まで崩れなかった理由は、実体経済の数字が朝より強く見えたから。', japan[2]['sources']),
            ('🇯🇵 日本・企業金融', 'ソフトバンクのOpenAI株担保ローン報道は、日本の大企業がまだAIへ積極的に資金を張っていることを示した。', '<strong>なぜ今か：</strong>AIは地政学や原油高の中でも成長ストーリーが崩れていない数少ない分野だから。金融市場も、そのテーマならレバレッジを許容しやすい。日本の午後材料はマクロだけでなく、リスクを取る企業金融の強さもあった。', japan[3]['sources']),
            ('🇯🇵 日本・通商政策', '日本はEUの域内優遇EVルール修正を促す方針。欧州需要回復局面で日本車勢の締め出しを避けたい。', '<strong>なぜ動いたか：</strong>欧州でEV需要が戻る中、現地生産優遇が固まると日本メーカーの販売機会が削られるから。物流費や電池コストが高い今、ルール面で不利になるのは避けたいという防衛的な動き。', japan[4]['sources']),
            ('🇯🇵 日本・エネルギー安全保障', '日本とサウジは代替輸送ルートで協力。ホルムズ依存を減らす動きが一段と具体化した。', '<strong>なぜ重要か：</strong>海峡が名目上開いても、保険、護衛、配船が戻らなければ実務上は正常化しないから。日本は備蓄対応だけでは足りず、迂回路そのものを増やす必要がある。', japan[5]['sources']),
        ]
        japan_cards = '\n'.join(story_card(t, h, b, s, ja=True) for t, h, b, s in japan_ja)
        global_cards = []
        region_map = {'North America': '北米', 'Europe': '欧州', 'Asia ex-Japan': 'アジア（日本除く）', 'Middle East & Africa': '中東・アフリカ', 'Latin America': '中南米', 'Oceania': 'オセアニア'}
        for region, items in global_regions.items():
            for _, headline, body, sources in items:
                global_cards.append(story_card(region_map[region], headline, body, sources, ja=True))
        global_cards = '\n'.join(global_cards)
        markets = '\n'.join([
            table_card('株式', '終値ベースの主要指数', ['指数', '水準', '日次', '週次', '月次', '年初来'], EQ_ROWS, '<strong>主な値動きの理由：</strong>日経平均は海外資金と円安で高値圏を維持したが、60,000円到達後の利益確定で伸び切れなかった。米株は決算が地政学を一時的に上回った。ブラジルは原油高と金融引き締め懸念の組み合わせが重荷。', market_sources),
            table_card('為替・金利', '通貨と金利の圧力点', ['指標', '水準', '日次', '週次', '月次', '年初来'], FX_ROWS, '<strong>重要ポイント：</strong>ドル円159円台は、日本が輸入インフレ問題をまだ解決できていないことを示す。ドル高と米金利の底堅さは、投資家がまだ完全な平和を織り込んでいない証拠。', market_sources),
            table_card('商品・暗号資産', 'コモディティとデジタル資産', ['資産', '価格', '日次', '週次', '月次', '年初来'], CMD_ROWS, '<strong>大きな動きの理由：</strong>銀はドル高とインフレヘッジ後退で2%以上下落。WTIはホルムズ物流の正常化が見えないため上昇。ビットコインは米株高を受けて買われたが、主役は依然として原油と為替。', market_sources),
            '''        <article class="card fade-in" data-image="">
          <span class="card-tag">健全性スコア</span>
          <h3 class="card-headline">58/100, 戻りはあるが見出しに弱い。</h3>
          <p class="card-body"><strong>なぜ58か：</strong>米株の高値維持、日本株の底堅さ、韓国の半導体主導の成長加速はプラス材料。ただし、ホルムズの摩擦で原油に再びリスクプレミアムがつき、ドルも強く、日銀も円の防波堤になっていない。つまり朝より良いが、まだ簡単に崩れうる地合い。</p>
          <div class="card-sources">\n''' + source_links(market_sources) + '''\n          </div>
        </article>'''
        ])
        predictions = '''        <article class="card fade-in collapsible" data-image="">
          <span class="card-tag">明日</span>
          <h3 class="card-headline">円がさらに弱くなっても日本株が持ちこたえるかが最大の焦点。</h3>
          <div class="tap-hint">タップして展開</div>
          <p class="card-body"><strong>なぜ重要か：</strong>円安は輸出株に追い風だが、行き過ぎると輸入燃料の痛みが勝ち始める。日銀がけん制しないままドル円が上振れると、明日は株高より円安不安が前面に出やすい。</p>
        </article>
        <article class="card fade-in collapsible" data-image="">
          <span class="card-tag">今週</span>
          <h3 class="card-headline">停戦見出しより、実際の海運正常化が進むかどうかが本当の試金石。</h3>
          <div class="tap-hint">タップして展開</div>
          <p class="card-body"><strong>なぜ重要か：</strong>タンカー航行、保険料、ルート安全が戻らなければ、原油高はインフレと消費不安を通じて残り続ける。そうなるとAIや半導体の強さがあっても、日本の上値は抑えられる。</p>
        </article>'''
        bottom_line = '午後の相場は、<strong>「停戦の見出し」と「物流まで含めた正常化」は別</strong>だと再確認した一日だった。日本株は海外資金と円安で支えられたが、その円安自体がエネルギー輸入コストを重くする。米株は決算で時間を稼ぎ、原油はホルムズの実務的な詰まりを理由に再び上昇した。<strong>要するに</strong>、午後は朝より改善したが、根本リスクはまだ片付いていない。'
        sub = '🇯🇵 日経平均は60,000円を試した後に利食いで押されたが高値圏を維持、円は日銀据え置き観測で159円近辺のまま · ソフトバンクのAI資金調達報道、日本のEU EV規則へのけん制、サウジとの代替輸送協力が午後の日本材料 · 米株は決算で高値維持、韓国は半導体で上振れ、欧州は燃料高でEVと屋根上太陽光需要が増加、原油はホルムズ物流不安で再上昇 · 健全性スコア: 58/100'
        footer = 'CEO午後ブリーフィング · Generated by Sanbot · 2026年4月23日（木）'
        body = f'''  <header class="masthead"><div class="lang-toggle"><a href="index.html">EN</a><span class="sep">/</span><a href="ja.html" class="active">JA</a></div><div class="masthead-inner"><div class="overline">午後のインテリジェンスブリーフ</div><div class="war-day-counter" id="war-day-badge">🔴 イラン戦争 — <span class="day-num" id="war-day-num">54</span>日目</div><br><div class="econ-countdown" id="econ-countdown">⏱ 経済ダメージ期間: <span class="countdown-num" id="econ-countdown-num">—</span></div><h1>CEO午後ブリーフィング</h1><div class="edition-date">{TODAY_JA} — 午後版</div><div class="edition-sub">{sub}</div><div class="divider-bar"></div></div></header><nav class="nav-pills"><a href="#japan" class="nav-pill">日本</a><a href="#global" class="nav-pill">世界</a><a href="#markets" class="nav-pill">マーケット</a><a href="#predictions" class="nav-pill">予測</a><a href="#bottomline" class="nav-pill">まとめ</a></nav><main class="container"><section class="section" id="japan"><div class="section-header"><div class="section-icon japan">🇯🇵</div><h2 class="section-title japan">日本アップデート — 詳細</h2></div><div class="cards">{japan_cards}</div></section><section class="section" id="global"><div class="section-header"><div class="section-icon">🌍</div><h2 class="section-title">世界 — 地域別</h2></div><div class="cards">{global_cards}</div></section><section class="section" id="markets"><div class="section-header"><div class="section-icon">📊</div><h2 class="section-title">マーケット・経済</h2></div><div class="cards">{markets}</div></section><section class="section" id="predictions"><div class="section-header"><div class="section-icon">🔮</div><h2 class="section-title">予測</h2></div><div class="cards">{predictions}</div></section><section class="section" id="bottomline"><div class="bottom-line"><h3>💡 まとめ</h3><p>{bottom_line}</p></div></section></main><footer class='footer'><p>{footer}</p><p style='margin-top: 0.5rem;'>データソース: Reuters, Kyodo, Yahoo Finance, Google News RSS</p></footer><script>document.querySelectorAll('.collapsible').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('expanded')));const needle=document.getElementById('gauge-needle');if(needle){{const score=58;const rotation=-90+(score/100)*180;setTimeout(()=>{{needle.style.transform=`rotate(${{rotation}}deg)`;}},300);}}</script><script>(function(){{var warStart=new Date(2026,2,1);var now=new Date();var dayNum=Math.floor((now-warStart)/86400000)+1;var el=document.getElementById('war-day-num');if(el)el.textContent=dayNum;var sixWeek=new Date(2026,4,2);var eightWeek=new Date(2026,4,16);var cdBox=document.getElementById('econ-countdown');if(cdBox){{if(now<sixWeek){{var daysLeft=Math.ceil((sixWeek-now)/86400000);cdBox.innerHTML='⏱ 経済ダメージ期間まで <span class="countdown-num">'+daysLeft+'</span> 日';}} else if(now<=eightWeek){{cdBox.style.background='#B94A48';cdBox.innerHTML='🔴 経済ダメージ期間 — <span class="countdown-num" style="color:#fff;">進行中</span>';}} else {{var weeksPast=Math.floor((now-new Date(2026,2,21))/(7*86400000));cdBox.style.background='#7f1d1d';cdBox.innerHTML='⚫ 原油高騰 '+weeksPast+' 週間 — ダメージ閾値超過';}}}})();</script><script src='audio-player.js'></script></body></html>'''
    return head + body


def patch_images_in_reviews():
    review_files = [
        'ai-review.html', 'ai-review-ja.html', 'energy-review.html', 'energy-review-ja.html',
        'health-wellness-review.html', 'health-wellness-review-ja.html', 'longevity-review.html',
        'longevity-review-ja.html', 'space-review.html', 'space-review-ja.html', 'sports-entertainment-review.html',
        'sports-entertainment-review-ja.html', 'vc-review.html', 'vc-review-ja.html'
    ]
    for name in review_files:
        path = BASE / name
        if not path.exists():
            continue
        soup = BeautifulSoup(path.read_text(), 'html.parser')
        changed = False
        for card in soup.select('article.card'):
            if card.get('data-image'):
                continue
            link = card.select_one('a[href]')
            if not link:
                continue
            img = og_image(link.get('href', ''))
            if img:
                card['data-image'] = img
                changed = True
        if changed:
            path.write_text(str(soup))


(BASE / 'index.html').write_text(build_index('en'))
(BASE / 'ja.html').write_text(build_index('ja'))
patch_images_in_reviews()
print('updated')
