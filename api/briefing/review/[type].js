const { fetchAndParse } = require('../../_parser');
module.exports = async (req, res) => {
  const { type } = req.query;
  try {
    const { parsed } = await fetchAndParse(`/${type}-review.html`);
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600');
    res.json(parsed);
  } catch (e) { res.status(404).json({ error: `Review "${type}" not found` }); }
};
