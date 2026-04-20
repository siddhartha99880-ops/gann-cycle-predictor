import Plot from 'react-plotly.js';

const PHASE_COLORS = {
  1: '#38bdf8', 2: '#4ade80', 3: '#22c55e',
  4: '#fbbf24', 5: '#f87171', 6: '#ef4444',
};

const PHASE_NAMES = {
  1: 'Accumulation', 2: 'Markup Begin', 3: 'Markup Acceleration',
  4: 'Distribution', 5: 'Markdown Begin', 6: 'Capitulation',
};

export default function Dashboard({ data, loading, symbol }) {
  if (loading && !data) {
    return (
      <div className="empty-state">
        <div className="loading-spinner" style={{ width: 32, height: 32, margin: '0 auto 16px' }} />
        <p>Analyzing {symbol}...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">◈</div>
        <p>Select a symbol and timeframe to begin analysis</p>
      </div>
    );
  }

  const phase = data.gann_cycle_phase || data.phase || 1;
  const phaseName = data.gann_cycle_name || data.phase_name || PHASE_NAMES[phase];
  const confidence = data.gann_cycle_confidence || data.confidence || 0;
  const bias = data.signal_bias || data.bias || 'SIDEWAYS';
  const scores = data.phase_scores || data.scores || {};
  const ohlcv = data.ohlcv || [];
  const chartData = {
    dates: ohlcv.map(r => r.date),
    open: ohlcv.map(r => r.open),
    high: ohlcv.map(r => r.high),
    low: ohlcv.map(r => r.low),
    close: ohlcv.map(r => r.close),
  };

  const biasClass = bias === 'BULLISH' ? 'badge-bullish' : bias === 'BEARISH' ? 'badge-bearish' : 'badge-sideways';

  // Build candlestick chart if available
  const hasChart = chartData.dates && chartData.dates.length > 0;

  return (
    <div>
      {/* Metrics Row */}
      <div className="grid-cols-4" style={{ marginBottom: 24 }}>
        <div className="metric-card">
          <div className="metric-label">Current Phase</div>
          <div className="metric-value" style={{ color: PHASE_COLORS[phase] }}>
            {phase}. {phaseName}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Confidence</div>
          <div className="metric-value">{confidence}%</div>
          <div style={{ marginTop: 8, height: 4, borderRadius: 2, background: 'var(--border-light)' }}>
            <div style={{ height: '100%', width: `${confidence}%`, borderRadius: 2, background: PHASE_COLORS[phase], transition: 'width 0.6s ease' }} />
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Signal Bias</div>
          <div className="metric-value">
            <span className={`signal-badge ${biasClass}`}>{bias}</span>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Next Phase</div>
          <div className="metric-value" style={{ fontSize: '1.1rem' }}>
            {data.next_phase_name || '—'}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4 }}>
            {data.transition_probability ? `${data.transition_probability}% probability` : ''}
          </div>
        </div>
      </div>

      {/* Signal Card */}
      <div className="signal-card" style={{ marginBottom: 24 }}>
        <div className="signal-header">
          <div className="signal-bias" style={{ color: PHASE_COLORS[phase] }}>
            {data.icon || '◈'} {phaseName}
          </div>
          <span className={`signal-badge ${biasClass}`}>{bias}</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 20 }}>
          {data.description || 'Analyzing market conditions...'}
        </p>
        <div className="signal-grid">
          <div className="signal-item">
            <span className="signal-item-label">Duration</span>
            <span className="signal-item-value">{data.duration || 0} bars</span>
          </div>
          <div className="signal-item">
            <span className="signal-item-label">VIX</span>
            <span className="signal-item-value">{data.vix ?? '—'}</span>
          </div>
          <div className="signal-item">
            <span className="signal-item-label">PCR</span>
            <span className="signal-item-value">{data.pcr ?? '—'}</span>
          </div>
          {data.entry_zone && (
            <div className="signal-item">
              <span className="signal-item-label">Entry Zone</span>
              <span className="signal-item-value text-green">₹{data.entry_zone}</span>
            </div>
          )}
          {data.stop_loss && (
            <div className="signal-item">
              <span className="signal-item-label">Stop Loss</span>
              <span className="signal-item-value text-red">₹{data.stop_loss}</span>
            </div>
          )}
          {data.targets && (
            <div className="signal-item">
              <span className="signal-item-label">Targets</span>
              <span className="signal-item-value">{data.targets}</span>
            </div>
          )}
        </div>
      </div>

      {/* Phase Scores */}
      <div className="grid-cols-2" style={{ marginBottom: 24 }}>
        {/* Chart */}
        <div className="chart-wrap">
          {hasChart ? (
            <Plot
              data={[{
                x: chartData.dates,
                open: chartData.open,
                high: chartData.high,
                low: chartData.low,
                close: chartData.close,
                type: 'candlestick',
                increasing: { line: { color: '#4ade80' } },
                decreasing: { line: { color: '#ef4444' } },
              }]}
              layout={{
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: { color: '#8b92a5', family: 'Inter' },
                margin: { t: 20, b: 40, l: 50, r: 20 },
                xaxis: { gridcolor: '#242730', showgrid: false },
                yaxis: { gridcolor: '#242730', title: 'Price' },
                height: 380,
                showlegend: false,
              }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: '100%' }}
            />
          ) : (
            <div className="empty-state" style={{ padding: '40px 0' }}>
              <p style={{ color: 'var(--text-muted)' }}>Chart data loading...</p>
            </div>
          )}
        </div>

        {/* Phase Scores Bar */}
        <div className="chart-wrap">
          <div className="card-title">Phase Scores</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {Object.entries(scores).map(([p, score]) => {
              const pNum = parseInt(p);
              const maxScore = { 1: 10, 2: 10, 3: 12, 4: 10, 5: 10, 6: 11 }[pNum] || 10;
              const pct = Math.min(100, (score / maxScore) * 100);
              return (
                <div key={p}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: 4 }}>
                    <span style={{ color: PHASE_COLORS[pNum], fontWeight: 500 }}>{PHASE_NAMES[pNum]}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{score}/{maxScore}</span>
                  </div>
                  <div style={{ height: 6, borderRadius: 3, background: 'var(--border-light)' }}>
                    <div style={{
                      height: '100%', borderRadius: 3,
                      width: `${pct}%`,
                      background: PHASE_COLORS[pNum],
                      transition: 'width 0.6s ease',
                      boxShadow: pNum === phase ? `0 0 8px ${PHASE_COLORS[pNum]}40` : 'none',
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
