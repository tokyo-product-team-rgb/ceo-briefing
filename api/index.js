module.exports = (req, res) => {
  res.json({
    service: 'CEO Briefing API',
    version: '1.0.0',
    endpoints: [
      { method: 'GET', path: '/api/briefing/latest', desc: 'Latest briefing (EN) — structured JSON' },
      { method: 'GET', path: '/api/briefing/latest-ja', desc: 'Latest briefing (JA) — structured JSON' },
      { method: 'GET', path: '/api/briefing/headlines', desc: 'Headlines only' },
      { method: 'GET', path: '/api/briefing/reviews', desc: 'List review types' },
      { method: 'GET', path: '/api/briefing/review/[type]', desc: 'Specific review (ai, vc, energy, etc.)' },
      { method: 'GET', path: '/api/briefing/raw', desc: 'Raw HTML of latest briefing' },
      { method: 'GET', path: '/api/health', desc: 'Health check' }
    ]
  });
};
