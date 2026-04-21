import Plot from 'react-plotly.js';

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

export default function Dashboard({ data, loading, symbol }) {
  if (loading && !data) {
    return (
      <div className="empty-state">
        <div className="loading-spinner" style={{ width: 36, height: 36, margin: '0 auto 20px' }} />
        <p style={{ fontSize: '0.92rem' }}>Running Gann Square of 9 analysis on <strong style={{ color: 'var(--accent-primary)' }}>{symbol}</strong>…</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">◈</div>
        <p>Select a symbol and timeframe to begin Gann Cycle analysis</p>
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
  const hasChart = chartData.dates && chartData.dates.length > 0;
  const phaseColor = PHASE_COLORS[phase];

  // Price data
  const price = data.price || 0;
  const priceChange = data.price_change || 0;
  const priceChangePct = data.price_change_pct || 0;

  return (
    <div>
      {/* ─── Price Header ─── */}
      <div style={{
        display: 'flex',
        alignItems: 'baseline',
        gap: 16,
        marginBottom: 24,
        padding: '0 4px',
      }}>
        <span style={{
          fontSize: '2rem',
          fontWeight: 800,
          fontFamily: "'JetBrains Mono', monospace",
          letterSpacing: '-0.03em',
        }}>
          ₹{price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
        </span>
        <span style={{
          fontSize: '1rem',
          fontWeight: 600,
          fontFamily: "'JetBrains Mono', monospace",
          color: priceChange >= 0 ? 'var(--success)' : 'var(--danger)',
        }}>
          {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)} ({priceChangePct >= 0 ? '+' : ''}{priceChangePct.toFixed(2)}%)
        </span>
      </div>

      {/* ─── Metrics Row ─── */}
      <div className="grid-cols-4" style={{ marginBottom: 24 }}>
        <div className="metric-card">
          <div className="metric-label">Current Phase</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: '1.4rem' }}>{PHASE_ICONS[phase]}</span>
            <div>
              <div className="metric-value" style={{ color: phaseColor, fontSize: '1.2rem' }}>
                {phaseName}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>
                Phase {phase} of 6
              </div>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Confidence Score</div>
          <div className="metric-value" style={{ color: phaseColor }}>
            {confidence}%
          </div>
          <div className="progress-bar">
            <div
              className="progress-bar-fill"
              style={{
                width: `${confidence}%`,
                background: `linear-gradient(90deg, ${phaseColor}, ${phaseColor}88)`,
                boxShadow: `0 0 8px ${phaseColor}40`,
              }}
            />
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Signal Bias</div>
          <div style={{ marginTop: 4 }}>
            <span className={`signal-badge ${biasClass}`} style={{ fontSize: '0.8rem', padding: '6px 16px' }}>{bias}</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 8 }}>
            {data.signal_strength || 'MODERATE'} conviction
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Next Phase</div>
          <div className="metric-value" style={{ fontSize: '1rem' }}>
            {data.next_phase_name || '—'}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 6 }}>
            {data.transition_probability ? (
              <span style={{
                padding: '2px 8px',
                borderRadius: 100,
                background: 'rgba(99, 131, 255, 0.08)',
                color: 'var(--accent-primary)',
                fontWeight: 600,
              }}>
                {data.transition_probability}% probability
              </span>
            ) : 'Transition pending'}
          </div>
        </div>
      </div>

      {/* ─── Signal Card ─── */}
      <div className="signal-card" style={{ marginBottom: 24 }}>
        <div className="signal-header">
          <div className="signal-bias" style={{ color: phaseColor }}>
            {PHASE_ICONS[phase]} {phaseName}
          </div>
          <span className={`signal-badge ${biasClass}`}>{bias}</span>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className="live-dot" />
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 500 }}>LIVE</span>
          </div>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: 20, lineHeight: 1.6, position: 'relative', zIndex: 1 }}>
          {data.description || 'Gann Square of 9 analysis in progress — monitoring price action relative to Gann angles and support/resistance levels.'}
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
          {data.options_strategy && (
            <div className="signal-item">
              <span className="signal-item-label">Options Strategy</span>
              <span className="signal-item-value text-blue">{data.options_strategy}</span>
            </div>
          )}
        </div>
      </div>

      {/* ─── Chart + Phase Scores ─── */}
      <div className="grid-cols-2" style={{ marginBottom: 24 }}>
        {/* Candlestick Chart */}
        <div className="chart-wrap" style={{ marginTop: 0 }}>
          <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Price Action</span>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 500, textTransform: 'none', letterSpacing: 0 }}>
              {ohlcv.length} bars
            </span>
          </div>
          {hasChart ? (
            <Plot
              data={[{
                x: chartData.dates,
                open: chartData.open,
                high: chartData.high,
                low: chartData.low,
                close: chartData.close,
                type: 'candlestick',
                increasing: { line: { color: '#34d399', width: 1 }, fillcolor: '#34d39920' },
                decreasing: { line: { color: '#f87171', width: 1 }, fillcolor: '#f8717120' },
              }]}
              layout={{
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: { color: '#4a5272', family: 'Inter', size: 11 },
                margin: { t: 10, b: 40, l: 55, r: 10 },
                xaxis: {
                  gridcolor: 'rgba(255,255,255,0.03)',
                  linecolor: 'rgba(255,255,255,0.06)',
                  showgrid: false,
                  rangeslider: { visible: false },
                },
                yaxis: {
                  gridcolor: 'rgba(255,255,255,0.03)',
                  linecolor: 'rgba(255,255,255,0.06)',
                  title: { text: 'Price (₹)', font: { size: 10, color: '#4a5272' } },
                  side: 'right',
                },
                height: 380,
                showlegend: false,
              }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: '100%' }}
            />
          ) : (
            <div className="empty-state" style={{ padding: '40px 0' }}>
              <p style={{ color: 'var(--text-muted)' }}>Awaiting price data…</p>
            </div>
          )}
        </div>

        {/* Phase Scores */}
        <div className="chart-wrap" style={{ marginTop: 0 }}>
          <div className="card-title">Gann Phase Scoring Matrix</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {Object.entries(scores).map(([p, score]) => {
              const pNum = parseInt(p);
              const maxScore = { 1: 10, 2: 10, 3: 12, 4: 10, 5: 10, 6: 11 }[pNum] || 10;
              const pct = Math.min(100, (score / maxScore) * 100);
              const isActive = pNum === phase;
              const color = PHASE_COLORS[pNum];
              return (
                <div key={p} style={{
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  background: isActive ? `${color}08` : 'transparent',
                  border: isActive ? `1px solid ${color}20` : '1px solid transparent',
                  transition: 'all 0.3s ease',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: 6 }}>
                    <span style={{ color, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                      {PHASE_ICONS[pNum]} {PHASE_NAMES[pNum]}
                      {isActive && (
                        <span style={{
                          padding: '1px 6px',
                          borderRadius: 100,
                          background: `${color}15`,
                          fontSize: '0.6rem',
                          fontWeight: 700,
                          letterSpacing: '0.04em',
                        }}>
                          ACTIVE
                        </span>
                      )}
                    </span>
                    <span style={{
                      color: isActive ? color : 'var(--text-muted)',
                      fontFamily: "'JetBrains Mono', monospace",
                      fontWeight: 600,
                      fontSize: '0.75rem',
                    }}>
                      {score}/{maxScore}
                    </span>
                  </div>
                  <div className="progress-bar" style={{ marginTop: 0, height: isActive ? 8 : 5 }}>
                    <div
                      className="progress-bar-fill"
                      style={{
                        width: `${pct}%`,
                        background: `linear-gradient(90deg, ${color}, ${color}99)`,
                        boxShadow: isActive ? `0 0 12px ${color}40` : 'none',
                      }}
                    />
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
