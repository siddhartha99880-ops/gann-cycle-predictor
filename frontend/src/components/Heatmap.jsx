import { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { api } from '../api';

const PHASE_COLORS = {
  1: '#38bdf8', 2: '#4ade80', 3: '#22c55e',
  4: '#fbbf24', 5: '#f87171', 6: '#ef4444',
};

const PHASE_NAMES = {
  1: 'Accumulation', 2: 'Markup Begin', 3: 'Markup Acceleration',
  4: 'Distribution', 5: 'Markdown Begin', 6: 'Capitulation',
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
        <div className="loading-spinner" style={{ width: 32, height: 32, margin: '0 auto 16px' }} />
        <p>Scanning all sectors...</p>
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

  // Phase distribution for pie chart
  const phaseCount = {};
  Object.values(results).forEach(r => {
    const p = r.phase || 1;
    phaseCount[p] = (phaseCount[p] || 0) + 1;
  });

  return (
    <div>
      {/* Heatmap Grid */}
      <div className="heatmap-grid" style={{ marginBottom: 24 }}>
        {Object.entries(results).map(([name, r]) => {
          const phase = r.phase || 1;
          const color = PHASE_COLORS[phase];
          return (
            <div
              key={name}
              className="heatmap-cell"
              style={{ background: `${color}08`, borderColor: `${color}30` }}
            >
              <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
                {name}
              </div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color, marginBottom: 4 }}>
                {PHASE_NAMES[phase]}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                <span>Confidence: {r.confidence || 0}%</span>
                <span className={`signal-badge ${r.bias === 'BULLISH' ? 'badge-bullish' : r.bias === 'BEARISH' ? 'badge-bearish' : 'badge-sideways'}`} style={{ fontSize: '0.68rem' }}>
                  {r.bias}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Phase Distribution Chart */}
      <div className="chart-wrap">
        <div className="card-title">Phase Distribution</div>
        <Plot
          data={[{
            labels: Object.keys(phaseCount).map(p => PHASE_NAMES[parseInt(p)]),
            values: Object.values(phaseCount),
            type: 'pie',
            marker: { colors: Object.keys(phaseCount).map(p => PHASE_COLORS[parseInt(p)]) },
            hole: 0.5,
            textinfo: 'label+value',
            textfont: { color: '#e2e4e9', family: 'Inter' },
          }]}
          layout={{
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#8b92a5', family: 'Inter' },
            margin: { t: 20, b: 20, l: 20, r: 20 },
            height: 340,
            showlegend: false,
          }}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: '100%' }}
        />
      </div>
    </div>
  );
}
