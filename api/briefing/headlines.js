const { fetchAndParse } = require('../_parser');
module.exports = async (req, res) => {
  try {
    const lang = req.query.lang || 'en';
    const page = lang === 'ja' ? '/ja.html' : '/index.html';
    const { parsed } = await fetchAndParse(page);
    const headlines = parsed.sections.flatMap(s =>
      s.stories.map(st => ({ section: s.title, headline: st.headline, tag: st.tag }))
    );
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600');
    res.json({ date: parsed.date, count: headlines.length, headlines });
  } catch (e) { res.status(500).json({ error: e.message }); }
};
