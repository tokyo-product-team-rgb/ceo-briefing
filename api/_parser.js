const { JSDOM } = require('jsdom');

const SOURCE_BASE = 'https://ceo-briefing.vercel.app';

async function fetchAndParse(path) {
  const url = `${SOURCE_BASE}${path}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.status}`);
  const html = await res.text();
  return { parsed: parseBriefing(html, path), html };
}

function extractTable(card) {
  const gaugeScore = card.querySelector('.gauge-score');
  if (gaugeScore) {
    const score = parseInt(gaugeScore.textContent.trim(), 10);
    const label = card.querySelector('.gauge-score-label')?.textContent?.trim() || '';
    const indicators = [];
    card.querySelectorAll('.indicator-item').forEach(item => {
      const name = item.querySelector('.indicator-name')?.textContent?.trim() || '';
      const sub = item.querySelector('.indicator-sub')?.textContent?.trim() || '';
      const emoji = item.querySelector('.indicator-value')?.textContent?.trim() || '';
      if (name) indicators.push({ name, detail: sub, icon: emoji });
    });
    return { score, label, indicators };
  }
  const table = card.querySelector('table');
  if (!table) return null;
  const columns = [];
  table.querySelectorAll('thead th').forEach(th => columns.push(th.textContent.trim()));
  if (!columns.length) return null;
  const keyMap = {
    'index': 'name', 'commodity': 'name', 'pair': 'name', 'country': 'name', 'asset': 'name',
    'level': 'value', 'price': 'value', 'rate': 'value', '10y yield': 'value',
    'daily': 'daily', 'weekly': 'weekly', 'monthly': 'monthly', 'ytd': 'ytd', 'signal': 'signal',
    '指数': 'name', '商品': 'name', '通貨ペア': 'name', '国': 'name', '資産': 'name',
    '水準': 'value', '価格': 'value', 'レート': 'value', '10年利回り': 'value',
    '日次': 'daily', '週次': 'weekly', '月次': 'monthly', '年初来': 'ytd', 'シグナル': 'signal'
  };
  const rows = [];
  table.querySelectorAll('tbody tr').forEach(tr => {
    const cells = tr.querySelectorAll('td');
    const row = {};
    cells.forEach((td, i) => {
      if (i < columns.length) {
        const key = keyMap[columns[i].toLowerCase()] || columns[i].toLowerCase().replace(/\s+/g, '_');
        row[key] = td.textContent.trim();
      }
    });
    if (Object.keys(row).length) rows.push(row);
  });
  return { columns, rows };
}

function parseSectionTable(section) {
  const table = section.querySelector('.data-table');
  if (!table) return null;
  const columns = [];
  table.querySelectorAll('thead th').forEach(th => columns.push(th.textContent.trim()));
  const rows = [];
  table.querySelectorAll('tbody tr').forEach(tr => {
    const cells = tr.querySelectorAll('td');
    const row = {};
    cells.forEach((td, i) => {
      if (i < columns.length) {
        const key = columns[i].toLowerCase().replace(/\s+/g, '_');
        row[key] = td.textContent.trim();
      }
    });
    if (Object.keys(row).length) rows.push(row);
  });
  return columns.length ? { columns, rows } : null;
}

function parseBriefing(html, filename) {
  const dom = new JSDOM(html);
  const doc = dom.window.document;

  const title = doc.querySelector('title')?.textContent || '';
  const dateMatch = title.match(/(\w+ \d+, \d{4})/);
  const date = dateMatch ? dateMatch[1] : filename;
  const editionDate = doc.querySelector('.edition-date')?.textContent?.trim() || '';
  const editionLabel = doc.querySelector('.edition-label')?.textContent?.trim() || '';

  const sections = [];
  doc.querySelectorAll('.section').forEach(section => {
    const sectionId = section.id || '';
    const sectionTitle = section.querySelector('.section-title, h2, h3')?.textContent?.trim() || '';

    const stories = [];
    section.querySelectorAll('.card').forEach(card => {
      const headline = card.querySelector('.card-headline')?.textContent?.trim() || '';
      const summary = card.querySelector('.card-summary, .card-body, p')?.textContent?.trim() || '';
      const tag = card.querySelector('.card-tag, .tag')?.textContent?.trim() || '';
      const meta = card.querySelector('.card-meta')?.textContent?.trim() || '';
      const bullets = [];
      card.querySelectorAll('li').forEach(li => bullets.push(li.textContent.trim()));
      const sources = [];
      card.querySelectorAll('.card-sources .source-link').forEach(a => {
        const name = a.textContent.replace(/[\s\u2197]+$/g, '').trim();
        const url = a.getAttribute('href') || '';
        if (name || url) sources.push({ name, url });
      });
      const imageUrl = card.querySelector('img')?.getAttribute('src')
        || card.getAttribute('data-image')
        || card.querySelector('[data-image]')?.getAttribute('data-image')
        || '';
      const tableData = extractTable(card);
      const isQuote = headline.startsWith('"') || headline.startsWith('\u201c');

      const story = {
        headline, summary, tag,
        bullets: bullets.slice(0, 10),
        sources,
        ...(imageUrl ? { image_url: imageUrl } : {}),
        ...(tableData ? { table: tableData } : {}),
        ...(meta ? { meta } : {}),
        ...(isQuote ? { quote: headline } : {})
      };
      if (headline) stories.push(story);
    });

    const sectionData = { id: sectionId, title: sectionTitle, stories };

    // Stat cards
    const statCards = section.querySelectorAll('.stat-card');
    if (statCards.length) {
      sectionData.stats = [];
      statCards.forEach(sc => {
        const value = sc.querySelector('.stat-value')?.textContent?.trim() || '';
        const labelText = sc.querySelector('.stat-label')?.textContent?.trim() || '';
        const labelMatch = labelText.match(/^([^(]+?)(?:\s*\((.+)\))?$/);
        const label = labelMatch ? labelMatch[1].trim() : labelText;
        const context = labelMatch && labelMatch[2] ? labelMatch[2].trim() : null;
        if (value) sectionData.stats.push({ value, label, ...(context ? { context } : {}) });
      });
    }

    // Section-level data tables
    const sectionTable = parseSectionTable(section);
    if (sectionTable) sectionData.table = sectionTable;

    // Fund cards
    const fundCards = section.querySelectorAll('.fund-card');
    if (fundCards.length) {
      sectionData.table = { columns: ['Fund', 'Amount', 'Focus'], rows: [] };
      fundCards.forEach(fc => {
        const name = fc.querySelector('.fund-name')?.textContent?.trim() || '';
        const value = fc.querySelector('.fund-size')?.textContent?.trim() || '';
        const focus = fc.querySelector('.fund-focus')?.textContent?.trim() || '';
        if (name) sectionData.table.rows.push({ name, value, focus });
      });
    }

    // Highlight box
    const highlightBox = section.querySelector('.highlight-box');
    if (highlightBox) {
      const ht = highlightBox.querySelector('.highlight-title')?.textContent?.trim() || '';
      const hp = highlightBox.querySelector('p')?.textContent?.trim() || '';
      sectionData.highlight = { title: ht, text: hp };
    }

    // Bottom line with takeaway
    const bottomLine = section.querySelector('.bottom-line');
    if (bottomLine) {
      const paragraphs = bottomLine.querySelectorAll('p');
      const texts = [];
      let takeaway = '';
      paragraphs.forEach(p => {
        texts.push(p.textContent.trim());
        if (p.getAttribute('style')?.includes('font-weight') || p.querySelector('strong')) {
          takeaway = p.textContent.trim();
        }
      });
      if (texts.length && !stories.length) {
        sectionData.stories.push({
          headline: sectionTitle || 'Bottom line',
          summary: texts.join(' '),
          tag: '', bullets: [], sources: [],
          ...(takeaway ? { takeaway } : {})
        });
      }
    }

    if (sectionTitle || stories.length || sectionData.stats || sectionData.table) {
      sections.push(sectionData);
    }
  });

  const bottomLine = doc.querySelector('#bottomline p, #bottomline .card-body, .bottom-line p')?.textContent?.trim() || '';
  return { date, editionDate, editionLabel, title, sections, bottomLine };
}

module.exports = { fetchAndParse, parseBriefing, SOURCE_BASE };
