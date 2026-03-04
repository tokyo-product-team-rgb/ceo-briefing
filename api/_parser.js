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
      if (headline) stories.push({ headline, summary: summary.substring(0, 500), tag, bullets: bullets.slice(0, 10) });
    });
    if (sectionTitle || stories.length) sections.push({ id: sectionId, title: sectionTitle, stories });
  });

  const bottomLine = doc.querySelector('#bottomline p, #bottomline .card-body')?.textContent?.trim() || '';
  return { date, editionDate, editionLabel, title, sections, bottomLine };
}

module.exports = { fetchAndParse, parseBriefing, SOURCE_BASE };
