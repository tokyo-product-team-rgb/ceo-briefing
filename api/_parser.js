const { JSDOM } = require('jsdom');

// When running on Vercel, fetch from own deployment
const SOURCE_BASE = process.env.VERCEL_URL
  ? `https://${process.env.VERCEL_URL}`
  : 'https://ceo-briefing.vercel.app';

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
    'daily': 'daily', 'weekly': 'weekly', 'monthly': 'monthly', 'ytd': 'ytd', 'signal': 'signal'
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
      const bullets = [];
      card.querySelectorAll('li').forEach(li => bullets.push(li.textContent.trim()));
      const imageUrl = card.querySelector('img')?.getAttribute('src')
        || card.getAttribute('data-image')
        || card.querySelector('[data-image]')?.getAttribute('data-image')
        || '';
      const tableData = extractTable(card);
      if (headline) stories.push({ headline, summary: summary, tag, bullets: bullets.slice(0, 10), ...(imageUrl ? { image_url: imageUrl } : {}) ...(tableData ? { table: tableData } : {}) });
    });
    if (sectionTitle || stories.length) sections.push({ id: sectionId, title: sectionTitle, stories });
  });

  const bottomLine = doc.querySelector('#bottomline p, #bottomline .card-body')?.textContent?.trim() || '';
  return { date, editionDate, editionLabel, title, sections, bottomLine };
}

module.exports = { fetchAndParse, parseBriefing, SOURCE_BASE };
