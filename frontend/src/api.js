const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export const api = {
  getSymbols: () => request('/api/symbols'),
  getPhase: (symbol, tf) => request(`/api/prediction?symbol=${encodeURIComponent(symbol)}&timeframe=${tf}`),
  getMultiTF: (symbol) => request(`/api/multi-timeframe?symbol=${encodeURIComponent(symbol)}`),
  getHeatmap: () => request('/api/heatmap').then(data => ({
    // Normalize: backend returns { indices: {...} }, frontend expects { results: {...} }
    results: data.indices || data.results || {},
    phase_distribution: data.phase_distribution || {},
  })),
  getAlerts: (symbol) => request(`/api/alerts?limit=30`),
  runBacktest: (data) => request('/api/backtest', { method: 'POST', body: JSON.stringify(data) }),
};
