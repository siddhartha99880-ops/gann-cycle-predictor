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
      {/* Controls */}
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
        <button className="btn btn-primary" onClick={runBacktest} disabled={loading}>
          {loading ? 'Running...' : '▶ Run Backtest'}
        </button>
      </div>

      {error && (
        <div className="card" style={{ borderColor: '#ef4444', marginBottom: 24 }}>
          <p style={{ color: '#f87171' }}>{error}</p>
        </div>
      )}

      {result && (
        <>
          {/* Metrics */}
          <div className="grid-cols-4" style={{ marginBottom: 24 }}>
            <div className="metric-card">
              <div className="metric-label">Total Trades</div>
              <div className="metric-value">{result.total_trades}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Win Rate</div>
              <div className="metric-value" style={{ color: result.win_rate >= 50 ? '#4ade80' : '#f87171' }}>
                {result.win_rate}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Total Return</div>
              <div className="metric-value" style={{ color: result.total_return >= 0 ? '#4ade80' : '#f87171' }}>
                {result.total_return > 0 ? '+' : ''}{result.total_return}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Sharpe Ratio</div>
              <div className="metric-value">{result.sharpe_ratio}</div>
            </div>
          </div>

          {/* More Metrics */}
          <div className="grid-cols-3" style={{ marginBottom: 24 }}>
            <div className="metric-card">
              <div className="metric-label">Winning Trades</div>
              <div className="metric-value text-green">{result.winning_trades}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Losing Trades</div>
              <div className="metric-value text-red">{result.losing_trades}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Max Drawdown</div>
              <div className="metric-value text-red">-{result.max_drawdown}%</div>
            </div>
          </div>

          {/* Equity Curve */}
          {result.equity_curve && result.equity_curve.length > 1 && (
            <div className="chart-wrap" style={{ marginBottom: 24 }}>
              <div className="card-title">Equity Curve</div>
              <Plot
                data={[{
                  y: result.equity_curve,
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#3b82f6', width: 2 },
                  fill: 'tozeroy',
                  fillcolor: 'rgba(59,130,246,0.06)',
                }]}
                layout={{
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'transparent',
                  font: { color: '#8b92a5', family: 'Inter' },
                  margin: { t: 10, b: 40, l: 60, r: 20 },
                  xaxis: { title: 'Bars', gridcolor: '#242730' },
                  yaxis: { title: 'Equity (₹)', gridcolor: '#242730' },
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
              <div className="card-title">Trade Log</div>
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
                      <td>{t.entry_date}</td>
                      <td>{t.exit_date}</td>
                      <td>₹{t.entry_price}</td>
                      <td>₹{t.exit_price}</td>
                      <td style={{ color: t.pnl_pct >= 0 ? '#4ade80' : '#f87171', fontWeight: 600 }}>
                        {t.pnl_pct > 0 ? '+' : ''}{t.pnl_pct}%
                      </td>
                      <td>{t.bars_held}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {!result && !loading && (
        <div className="empty-state">
          <div className="empty-state-icon">⟐</div>
          <p>Configure parameters and click Run Backtest</p>
        </div>
      )}
    </div>
  );
}
