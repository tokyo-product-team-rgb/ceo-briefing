const { fetchAndParse } = require('../_parser');
module.exports = async (req, res) => {
  try {
    const { html } = await fetchAndParse('/index.html');
    res.setHeader('Content-Type', 'text/html');
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600');
    res.send(html);
  } catch (e) { res.status(500).json({ error: e.message }); }
};
