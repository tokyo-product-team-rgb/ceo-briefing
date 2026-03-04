module.exports = (req, res) => {
  res.json({ status: 'ok', service: 'ceo-briefing', timestamp: new Date().toISOString() });
};
