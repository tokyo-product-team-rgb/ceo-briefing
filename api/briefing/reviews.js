module.exports = (req, res) => {
  const types = ['ai', 'vc', 'energy', 'health-wellness', 'longevity', 'space', 'sports-entertainment'];
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.json({ reviews: types.map(t => ({ type: t, url: `/api/briefing/review/${t}` })) });
};
