import { useState, useEffect } from 'react';
import { api } from '../api';

const PHASE_COLORS = {
  1: '#38bdf8', 2: '#4ade80', 3: '#22c55e',
  4: '#fbbf24', 5: '#f87171', 6: '#ef4444',
};

export default function MultiTF({ symbol }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getMultiTF(symbol)
      .then(setData)
      .catch(err => console.error('MTF error:', err))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) {
    return (
      <div className="empty-state">
        <div className="loading-spinner" style={{ width: 32, height: 32, margin: '0 auto 16px' }} />
        <p>Running multi-timeframe analysis for {symbol}...</p>
      </div>
    );
  }

  if (!data || !data.results) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">◫</div>
        <p>No multi-timeframe data available</p>
      </div>
    );
  }

  const { results, confluence } = data;

  return (
    <div>
      {/* Confluence Metrics */}
      <div className="grid-cols-4" style={{ marginBottom: 24 }}>
        <div className="metric-card">
          <div className="metric-label">Bullish TFs</div>
          <div className="metric-value text-green">{confluence?.bullish_count || 0}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Bearish TFs</div>
          <div className="metric-value text-red">{confluence?.bearish_count || 0}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Alignment</div>
          <div className="metric-value">{confluence?.alignment_score || 0}%</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Strength</div>
          <div className="metric-value" style={{ color: confluence?.strength === 'STRONG' ? '#4ade80' : confluence?.strength === 'MODERATE' ? '#fbbf24' : '#f87171' }}>
            {confluence?.strength || '—'}
          </div>
        </div>
      </div>

      {/* TF Table */}
      <div className="card" style={{ marginBottom: 24 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Timeframe</th>
              <th>Phase</th>
              <th>Confidence</th>
              <th>Bias</th>
              <th>Next Phase</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(results).map(([tf, r]) => (
              <tr key={tf}>
                <td style={{ fontWeight: 600 }}>{tf}</td>
                <td style={{ color: PHASE_COLORS[r.phase] }}>{r.phase}. {r.phase_name}</td>
                <td>{r.confidence}%</td>
                <td>
                  <span className={`signal-badge ${r.bias === 'BULLISH' ? 'badge-bullish' : r.bias === 'BEARISH' ? 'badge-bearish' : 'badge-sideways'}`}>
                    {r.bias}
                  </span>
                </td>
                <td style={{ color: 'var(--text-muted)' }}>{r.next_phase_name || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Confluence Verdict */}
      <div className="signal-card">
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
            Multi-TF Confluence Verdict
          </div>
          <div style={{
            fontSize: '1.8rem', fontWeight: 700,
            color: confluence?.dominant_bias === 'BULLISH' ? '#4ade80' : confluence?.dominant_bias === 'BEARISH' ? '#f87171' : '#fbbf24'
          }}>
            {confluence?.dominant_bias || 'SIDEWAYS'}
          </div>
          <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: 4 }}>
            {confluence?.bullish_count || 0} bullish / {confluence?.bearish_count || 0} bearish across {confluence?.total || 0} timeframes
          </div>
        </div>
      </div>
    </div>
  );
}
