import { useState } from 'react';
import Plot from 'react-plotly.js';
import { api } from '../api';

export default function Backtest({ symbols }) {
  const [symbol, setSymbol] = useState(symbols[0] || 'NIFTY 50');
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2026-04-20');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.runBacktest({ symbol, start_date: startDate, end_date: endDate, timeframe: '1d' });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* ─── Controls ─── */}
      <div className="bt-controls">
        <div className="control-group">
          <label className="control-label">Symbol</label>
          <select className="control-select" value={symbol} onChange={e => setSymbol(e.target.value)}>
            {symbols.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="control-group">
          <label className="control-label">Start Date</label>
          <input type="date" className="control-input" value={startDate} onChange={e => setStartDate(e.target.value)} />
        </div>
        <div className="control-group">
          <label className="control-label">End Date</label>
          <input type="date" className="control-input" value={endDate} onChange={e => setEndDate(e.target.value)} />
        </div>
        <button className="btn btn-primary" onClick={runBacktest} disabled={loading} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {loading && <span className="loading-spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />}
          {loading ? 'Running Engine…' : '▶ Run Backtest'}
        </button>
      </div>

      {/* ─── Error ─── */}
      {error && (
        <div style={{
          padding: '16px 20px',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(248, 113, 113, 0.06)',
          border: '1px solid rgba(248, 113, 113, 0.15)',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}>
          <span style={{ fontSize: '1.1rem' }}>⚠️</span>
          <p style={{ color: '#f87171', fontSize: '0.88rem', margin: 0 }}>{error}</p>
        </div>
      )}

      {/* ─── Results ─── */}
      {result && (
        <>
          {/* Primary Metrics */}
          <div className="grid-cols-4" style={{ marginBottom: 24 }}>
            <div className="metric-card">
              <div className="metric-label">Total Trades</div>
              <div className="metric-value">{result.total_trades}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Win Rate</div>
              <div className="metric-value" style={{ color: result.win_rate >= 50 ? 'var(--success)' : 'var(--danger)' }}>
                {result.win_rate}%
              </div>
              <div className="progress-bar">
                <div className="progress-bar-fill" style={{
                  width: `${result.win_rate}%`,
                  background: result.win_rate >= 50
                    ? 'linear-gradient(90deg, #34d399, #34d39988)'
                    : 'linear-gradient(90deg, #f87171, #f8717188)',
                }} />
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Total Return</div>
              <div className="metric-value" style={{ color: result.total_return >= 0 ? 'var(--success)' : 'var(--danger)' }}>
                {result.total_return > 0 ? '+' : ''}{result.total_return}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Sharpe Ratio</div>
              <div className="metric-value" style={{
                color: result.sharpe_ratio >= 1.5 ? 'var(--success)' :
                  result.sharpe_ratio >= 0.5 ? 'var(--warning)' : 'var(--danger)'
              }}>
                {result.sharpe_ratio}
              </div>
            </div>
          </div>

          {/* Secondary Metrics */}
          <div className="grid-cols-3" style={{ marginBottom: 24 }}>
            <div className="metric-card">
              <div className="metric-label">Winning Trades</div>
              <div className="metric-value text-green">{result.winning_trades}</div>
              <div style={{
                marginTop: 6,
                fontSize: '0.72rem',
                color: 'var(--text-muted)',
                fontFamily: "'JetBrains Mono', monospace",
              }}>
                Avg gain: {result.avg_win || '—'}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Losing Trades</div>
              <div className="metric-value text-red">{result.losing_trades}</div>
              <div style={{
                marginTop: 6,
                fontSize: '0.72rem',
                color: 'var(--text-muted)',
                fontFamily: "'JetBrains Mono', monospace",
              }}>
                Avg loss: {result.avg_loss || '—'}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Max Drawdown</div>
              <div className="metric-value text-red">-{result.max_drawdown}%</div>
              <div className="progress-bar">
                <div className="progress-bar-fill" style={{
                  width: `${Math.min(100, result.max_drawdown * 2)}%`,
                  background: 'linear-gradient(90deg, #f87171, #dc2626)',
                }} />
              </div>
            </div>
          </div>

          {/* Equity Curve */}
          {result.equity_curve && result.equity_curve.length > 1 && (
            <div className="chart-wrap" style={{ marginBottom: 24 }}>
              <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Equity Curve</span>
                <span style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '0.7rem',
                  color: result.total_return >= 0 ? 'var(--success)' : 'var(--danger)',
                  fontWeight: 600,
                  textTransform: 'none',
                  letterSpacing: 0,
                }}>
                  {result.total_return >= 0 ? '+' : ''}{result.total_return}% return
                </span>
              </div>
              <Plot
                data={[{
                  y: result.equity_curve,
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#6383ff', width: 2, shape: 'spline' },
                  fill: 'tozeroy',
                  fillcolor: 'rgba(99, 131, 255, 0.04)',
                }]}
                layout={{
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'transparent',
                  font: { color: '#4a5272', family: 'Inter', size: 11 },
                  margin: { t: 10, b: 40, l: 60, r: 10 },
                  xaxis: {
                    title: { text: 'Trade #', font: { size: 10, color: '#4a5272' } },
                    gridcolor: 'rgba(255,255,255,0.03)',
                    showgrid: false,
                  },
                  yaxis: {
                    title: { text: 'Equity (₹)', font: { size: 10, color: '#4a5272' } },
                    gridcolor: 'rgba(255,255,255,0.03)',
                    side: 'right',
                  },
                  height: 340,
                  showlegend: false,
                }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%' }}
              />
            </div>
          )}

          {/* Trade Log */}
          {result.trade_log && result.trade_log.length > 0 && (
            <div className="card">
              <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Trade Log</span>
                <span style={{
                  fontSize: '0.65rem',
                  color: 'var(--text-muted)',
                  fontWeight: 500,
                  textTransform: 'none',
                  letterSpacing: 0
                }}>
                  Showing {Math.min(50, result.trade_log.length)} of {result.trade_log.length}
                </span>
              </div>
              <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Entry Date</th>
                      <th>Exit Date</th>
                      <th>Entry ₹</th>
                      <th>Exit ₹</th>
                      <th>P&L %</th>
                      <th>Bars</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trade_log.slice(0, 50).map((t, i) => (
                      <tr key={i}>
                        <td>
                          <span className={`signal-badge ${t.type === 'LONG' ? 'badge-bullish' : 'badge-bearish'}`}>
                            {t.type}
                          </span>
                        </td>
                        <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.8rem' }}>{t.entry_date}</td>
                        <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.8rem' }}>{t.exit_date}</td>
                        <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.82rem' }}>₹{t.entry_price}</td>
                        <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.82rem' }}>₹{t.exit_price}</td>
                        <td style={{
                          color: t.pnl_pct >= 0 ? 'var(--success)' : 'var(--danger)',
                          fontWeight: 700,
                          fontFamily: "'JetBrains Mono', monospace",
                          fontSize: '0.82rem',
                        }}>
                          {t.pnl_pct > 0 ? '+' : ''}{t.pnl_pct}%
                        </td>
                        <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                          {t.bars_held}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* ─── Empty State ─── */}
      {!result && !loading && (
        <div style={{
          textAlign: 'center',
          padding: '80px 20px',
        }}>
          <div style={{
            width: 80,
            height: 80,
            borderRadius: 'var(--radius-lg)',
            background: 'rgba(99, 131, 255, 0.06)',
            border: '1px solid rgba(99, 131, 255, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px',
            fontSize: '2rem',
          }}>
            ⟐
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: 360, margin: '0 auto', lineHeight: 1.6 }}>
            Configure the symbol and date range above, then click <strong style={{ color: 'var(--accent-primary)' }}>Run Backtest</strong> to evaluate Gann Cycle strategy performance.
          </p>
        </div>
      )}
    </div>
  );
}
