module.exports = (req, res) => {
  const lang = req.query.lang || 'en';
  const types = ['ai', 'vc', 'energy', 'health-wellness', 'longevity', 'space', 'sports-entertainment'];

  const jaLabels = {
    'ai': 'AI',
    'vc': 'VC',
    'energy': 'エネルギー',
    'health-wellness': '健康・ウェルネス',
    'longevity': '長寿',
    'space': '宇宙',
    'sports-entertainment': 'スポーツ・エンタメ'
  };

  const reviews = types.map(t => ({
    type: t,
    label: lang === 'ja' ? (jaLabels[t] || t) : t,
    url: `/api/briefing/review/${t}${lang === 'ja' ? '?lang=ja' : ''}`
  }));

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.json({ reviews });
};
