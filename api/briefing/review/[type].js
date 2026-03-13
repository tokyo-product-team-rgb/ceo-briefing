const { fetchAndParse } = require('../../_parser');
module.exports = async (req, res) => {
  const { type, lang } = req.query;
  try {
    // Try Japanese version first if requested, fall back to English
    let parsed;
    if (lang === 'ja') {
      try {
        ({ parsed } = await fetchAndParse(`/${type}-review-ja.html`));
      } catch {
        // Japanese review page doesn't exist yet — fall back to English
        ({ parsed } = await fetchAndParse(`/${type}-review.html`));
        parsed._langFallback = 'en';
      }
    } else {
      ({ parsed } = await fetchAndParse(`/${type}-review.html`));
    }
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600');
    res.json(parsed);
  } catch (e) { res.status(404).json({ error: `Review "${type}" not found` }); }
};
