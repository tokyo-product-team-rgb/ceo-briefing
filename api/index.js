module.exports = (req, res) => {
  res.json({
    service: 'CEO Briefing API',
    version: '1.1.0',
    endpoints: [
      { method: 'GET', path: '/api/briefing/latest', desc: 'Latest briefing — add ?lang=ja for Japanese' },
      { method: 'GET', path: '/api/briefing/latest-ja', desc: 'Latest briefing (JA) — backwards compat' },
      { method: 'GET', path: '/api/briefing/headlines', desc: 'Headlines — add ?lang=ja for Japanese' },
      { method: 'GET', path: '/api/briefing/reviews', desc: 'List review types — add ?lang=ja for translated labels' },
      { method: 'GET', path: '/api/briefing/review/[type]', desc: 'Specific review — add ?lang=ja for Japanese' },
      { method: 'GET', path: '/api/briefing/raw', desc: 'Raw HTML of latest briefing' },
      { method: 'GET', path: '/api/health', desc: 'Health check' }
    ],
    params: {
      lang: 'Language code: "en" (default) or "ja". Supported on latest, headlines, reviews, and review/[type].'
    }
  });
};
