import { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
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

export default function Heatmap() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getHeatmap()
      .then(setData)
      .catch(err => console.error('Heatmap error:', err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="empty-state">
        <div className="loading-spinner" style={{ width: 36, height: 36, margin: '0 auto 20px' }} />
        <p>Scanning all sector indices with Gann engine…</p>
      </div>
    );
  }

  if (!data || !data.results) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">▦</div>
        <p>No heatmap data available</p>
      </div>
    );
  }

  const results = data.results;
  const totalIndices = Object.keys(results).length;

  // Phase distribution for donut chart
  const phaseCount = {};
  Object.values(results).forEach(r => {
    const p = r.phase || 1;
    phaseCount[p] = (phaseCount[p] || 0) + 1;
  });

  // Calculate bullish/bearish ratio
  const bullishCount = Object.values(results).filter(r => r.bias === 'BULLISH').length;
  const bearishCount = Object.values(results).filter(r => r.bias === 'BEARISH').length;

  return (
    <div>
      {/* ─── Summary Strip ─── */}
      <div className="grid-cols-3" style={{ marginBottom: 24 }}>
        <div className="metric-card">
          <div className="metric-label">Sectors Analyzed</div>
          <div className="metric-value">{totalIndices}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Bullish Sectors</div>
          <div className="metric-value text-green">{bullishCount}</div>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{
              width: `${(bullishCount / (totalIndices || 1)) * 100}%`,
              background: 'linear-gradient(90deg, #34d399, #34d39988)',
            }} />
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Bearish Sectors</div>
          <div className="metric-value text-red">{bearishCount}</div>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{
              width: `${(bearishCount / (totalIndices || 1)) * 100}%`,
              background: 'linear-gradient(90deg, #f87171, #f8717188)',
            }} />
          </div>
        </div>
      </div>

      {/* ─── Heatmap Grid ─── */}
      <div className="heatmap-grid" style={{ marginBottom: 24 }}>
        {Object.entries(results).map(([name, r], i) => {
          const phase = r.phase || 1;
          const color = PHASE_COLORS[phase];
          return (
            <div
              key={name}
              className="heatmap-cell"
              style={{
                background: `linear-gradient(135deg, ${color}06, ${color}03)`,
                borderColor: `${color}18`,
                animationDelay: `${i * 0.05}s`,
                animation: 'fadeInUp 0.4s var(--ease-smooth) forwards',
              }}
            >
              {/* Header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: 14,
              }}>
                <div style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  color: 'var(--text-secondary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}>
                  {name}
                </div>
                <span style={{ fontSize: '1.1rem' }}>{PHASE_ICONS[phase]}</span>
              </div>

              {/* Phase Name */}
              <div style={{
                fontSize: '1.1rem',
                fontWeight: 700,
                color,
                marginBottom: 6,
                letterSpacing: '-0.01em',
              }}>
                {PHASE_NAMES[phase]}
              </div>

              {/* Confidence Bar */}
              <div style={{ marginBottom: 12 }}>
                <div className="progress-bar" style={{ height: 4, marginTop: 0 }}>
                  <div className="progress-bar-fill" style={{
                    width: `${r.confidence || 0}%`,
                    background: color,
                  }} />
                </div>
              </div>

              {/* Footer */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <span style={{
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)',
                  fontFamily: "'JetBrains Mono', monospace",
                }}>
                  {r.confidence || 0}% conf
                </span>
                <span className={`signal-badge ${r.bias === 'BULLISH' ? 'badge-bullish' : r.bias === 'BEARISH' ? 'badge-bearish' : 'badge-sideways'}`}
                  style={{ fontSize: '0.62rem', padding: '3px 8px' }}>
                  {r.bias}
                </span>
              </div>

              {/* Duration and Next Phase */}
              <div style={{
                marginTop: 10,
                paddingTop: 10,
                borderTop: `1px solid ${color}10`,
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.68rem',
                color: 'var(--text-muted)',
              }}>
                <span>{r.duration || 0} bars</span>
                <span>→ {r.next_phase_name || '—'}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* ─── Phase Distribution Donut ─── */}
      <div className="chart-wrap">
        <div className="card-title">Phase Distribution Across Sectors</div>
        <Plot
          data={[{
            labels: Object.keys(phaseCount).map(p => `${PHASE_ICONS[parseInt(p)]} ${PHASE_NAMES[parseInt(p)]}`),
            values: Object.values(phaseCount),
            type: 'pie',
            marker: {
              colors: Object.keys(phaseCount).map(p => PHASE_COLORS[parseInt(p)]),
              line: { color: 'rgba(8, 9, 12, 0.8)', width: 2 },
            },
            hole: 0.55,
            textinfo: 'label+value',
            textposition: 'outside',
            textfont: { color: '#8892b0', family: 'Inter', size: 12 },
            hoverinfo: 'label+value+percent',
            sort: false,
          }]}
          layout={{
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#4a5272', family: 'Inter' },
            margin: { t: 20, b: 20, l: 40, r: 40 },
            height: 360,
            showlegend: false,
            annotations: [{
              text: `<b>${totalIndices}</b><br>Sectors`,
              showarrow: false,
              font: { size: 16, color: '#eaecf5', family: 'Inter' },
              x: 0.5,
              y: 0.5,
            }],
          }}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: '100%' }}
        />
      </div>
    </div>
  );
}
