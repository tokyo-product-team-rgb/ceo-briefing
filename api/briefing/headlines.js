const { fetchAndParse } = require('../_parser');
module.exports = async (req, res) => {
  try {
    const { parsed } = await fetchAndParse('/index.html');
    const headlines = parsed.sections.flatMap(s =>
      s.stories.map(st => ({ section: s.title, headline: st.headline, tag: st.tag }))
    );
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600');
    res.json({ date: parsed.date, count: headlines.length, headlines });
  } catch (e) { res.status(500).json({ error: e.message }); }
};
