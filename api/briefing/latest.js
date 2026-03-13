const { fetchAndParse } = require('../_parser');
module.exports = async (req, res) => {
  try {
    const lang = req.query.lang || 'en';
    const page = lang === 'ja' ? '/ja.html' : '/index.html';
    const { parsed } = await fetchAndParse(page);
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600');
    res.json(parsed);
  } catch (e) { res.status(500).json({ error: e.message }); }
};
