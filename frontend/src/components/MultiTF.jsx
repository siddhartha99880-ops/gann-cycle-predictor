import { useState, useEffect } from 'react';
import { api } from '../api';

const PHASE_COLORS = {
  1: '#38bdf8', 2: '#34d399', 3: '#10b981',
  4: '#fbbf24', 5: '#f87171', 6: '#dc2626',
};

const PHASE_NAMES = {
  1: 'Accumulation', 2: 'Markup Begin', 3: 'Markup Acceleration',
  4: 'Distribution', 5: 'Markdown Begin', 6: 'Capitulation',
};

const PHASE_ICONS = {
  1: '🟢', 2: '🚀', 3: '📈', 4: '⚠️', 5: '📉', 6: '🔴',
};

const TF_ORDER = ['5m', '15m', '1h', '1d', '1wk'];

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
        <div className="loading-spinner" style={{ width: 36, height: 36, margin: '0 auto 20px' }} />
        <p>Running multi-timeframe Gann analysis for <strong style={{ color: 'var(--accent-primary)' }}>{symbol}</strong>…</p>
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
  const sortedTFs = TF_ORDER.filter(tf => results[tf]);

  // Calculate overall alignment visual
  const alignmentScore = confluence?.alignment_score || 0;
  const strengthColor = confluence?.strength === 'STRONG' ? '#34d399' :
    confluence?.strength === 'MODERATE' ? '#fbbf24' : '#f87171';

  return (
    <div>
      {/* ─── Confluence Summary ─── */}
      <div className="grid-cols-4" style={{ marginBottom: 24 }}>
        <div className="metric-card">
          <div className="metric-label">Bullish Timeframes</div>
          <div className="metric-value text-green">{confluence?.bullish_count || 0}</div>
          <div className="progress-bar" style={{ marginTop: 8 }}>
            <div className="progress-bar-fill" style={{
              width: `${((confluence?.bullish_count || 0) / (confluence?.total || 5)) * 100}%`,
              background: 'linear-gradient(90deg, #34d399, #34d39988)',
            }} />
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Bearish Timeframes</div>
          <div className="metric-value text-red">{confluence?.bearish_count || 0}</div>
          <div className="progress-bar" style={{ marginTop: 8 }}>
            <div className="progress-bar-fill" style={{
              width: `${((confluence?.bearish_count || 0) / (confluence?.total || 5)) * 100}%`,
              background: 'linear-gradient(90deg, #f87171, #f8717188)',
            }} />
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Alignment Score</div>
          <div className="metric-value" style={{ color: 'var(--accent-primary)' }}>{alignmentScore}%</div>
          <div className="progress-bar" style={{ marginTop: 8 }}>
            <div className="progress-bar-fill" style={{
              width: `${alignmentScore}%`,
              background: 'var(--accent-gradient)',
            }} />
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Signal Strength</div>
          <div className="metric-value" style={{ color: strengthColor }}>
            {confluence?.strength || '—'}
          </div>
          <div style={{
            marginTop: 8,
            padding: '3px 10px',
            borderRadius: 100,
            background: `${strengthColor}12`,
            border: `1px solid ${strengthColor}20`,
            display: 'inline-block',
            fontSize: '0.65rem',
            fontWeight: 600,
            color: strengthColor,
          }}>
            {confluence?.total || 0} timeframes analyzed
          </div>
        </div>
      </div>

      {/* ─── Timeframe Breakdown ─── */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title" style={{ marginBottom: 0 }}>Timeframe Breakdown</div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Timeframe</th>
              <th>Phase</th>
              <th>Confidence</th>
              <th>Bias</th>
              <th>Duration</th>
              <th>Next Phase</th>
            </tr>
          </thead>
          <tbody>
            {sortedTFs.map((tf, i) => {
              const r = results[tf];
              const color = PHASE_COLORS[r.phase];
              return (
                <tr key={tf} style={{ animationDelay: `${i * 0.05}s` }}>
                  <td>
                    <span style={{
                      fontWeight: 700,
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: '0.82rem',
                    }}>
                      {r.timeframe_label || tf}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{
                        width: 8, height: 8,
                        borderRadius: '50%',
                        background: color,
                        boxShadow: `0 0 6px ${color}60`,
                        display: 'inline-block',
                        flexShrink: 0,
                      }} />
                      <span style={{ color, fontWeight: 600, fontSize: '0.84rem' }}>
                        {PHASE_ICONS[r.phase]} {r.phase_name}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 600, fontSize: '0.84rem' }}>
                        {r.confidence}%
                      </span>
                      <div style={{
                        width: 50, height: 4,
                        borderRadius: 2,
                        background: 'rgba(255,255,255,0.04)',
                        overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%',
                          width: `${r.confidence}%`,
                          borderRadius: 2,
                          background: color,
                        }} />
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={`signal-badge ${r.bias === 'BULLISH' ? 'badge-bullish' : r.bias === 'BEARISH' ? 'badge-bearish' : 'badge-sideways'}`}>
                      {r.bias}
                    </span>
                  </td>
                  <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.82rem' }}>
                    {r.duration || 0} bars
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                    {r.next_phase_name || '—'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ─── Confluence Verdict ─── */}
      <div className="signal-card">
        <div style={{ textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <div style={{
            fontSize: '0.68rem',
            fontWeight: 700,
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            marginBottom: 12,
          }}>
            Multi-Timeframe Confluence Verdict
          </div>
          <div style={{
            fontSize: '2.2rem',
            fontWeight: 800,
            letterSpacing: '-0.02em',
            color: confluence?.dominant_bias === 'BULLISH' ? '#34d399' :
              confluence?.dominant_bias === 'BEARISH' ? '#f87171' : '#fbbf24',
            textShadow: confluence?.dominant_bias === 'BULLISH' ? '0 0 30px rgba(52,211,153,0.2)' :
              confluence?.dominant_bias === 'BEARISH' ? '0 0 30px rgba(248,113,113,0.2)' : '0 0 30px rgba(251,191,36,0.2)',
          }}>
            {confluence?.dominant_bias || 'SIDEWAYS'}
          </div>
          <div style={{
            fontSize: '0.86rem',
            color: 'var(--text-secondary)',
            marginTop: 8,
          }}>
            {confluence?.bullish_count || 0} bullish · {confluence?.bearish_count || 0} bearish · {confluence?.total || 0} timeframes
          </div>
          <div style={{
            marginTop: 16,
            display: 'inline-block',
            padding: '6px 18px',
            borderRadius: 100,
            background: `${strengthColor}10`,
            border: `1px solid ${strengthColor}20`,
            fontSize: '0.75rem',
            fontWeight: 600,
            color: strengthColor,
          }}>
            {alignmentScore}% alignment · {confluence?.strength || 'N/A'} signal
          </div>
        </div>
      </div>
    </div>
  );
}
