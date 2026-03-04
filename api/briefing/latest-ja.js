const { fetchAndParse } = require('../_parser');
module.exports = async (req, res) => {
  try {
    const { parsed } = await fetchAndParse('/ja.html');
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600');
    res.json(parsed);
  } catch (e) { res.status(500).json({ error: e.message }); }
};
