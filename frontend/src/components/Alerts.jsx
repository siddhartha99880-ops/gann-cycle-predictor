import { useState, useEffect } from 'react';
import { api } from '../api';

export default function Alerts({ symbol }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getAlerts(symbol)
      .then(data => setAlerts(data.alerts || []))
      .catch(err => console.error('Alerts error:', err))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) {
    return (
      <div className="empty-state">
        <div className="loading-spinner" style={{ width: 32, height: 32, margin: '0 auto 16px' }} />
        <p>Fetching alerts for {symbol}...</p>
      </div>
    );
  }

  if (!alerts || alerts.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">◉</div>
        <p>No alerts generated yet. Run an analysis to trigger alerts.</p>
      </div>
    );
  }

  const severityColor = (sev) => {
    if (sev === 'HIGH' || sev === 'CRITICAL') return '#ef4444';
    if (sev === 'MEDIUM') return '#fbbf24';
    return '#38bdf8';
  };

  return (
    <div className="card">
      <table className="data-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Symbol</th>
            <th>Type</th>
            <th>Severity</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((a, i) => (
            <tr key={i}>
              <td style={{ whiteSpace: 'nowrap' }}>{a.timestamp || '—'}</td>
              <td style={{ fontWeight: 600 }}>{a.symbol || symbol}</td>
              <td>{a.type || '—'}</td>
              <td>
                <span style={{
                  padding: '3px 10px', borderRadius: 100, fontSize: '0.72rem', fontWeight: 600,
                  background: `${severityColor(a.severity)}15`, color: severityColor(a.severity),
                }}>
                  {a.severity || 'INFO'}
                </span>
              </td>
              <td style={{ color: 'var(--text-secondary)' }}>{a.message || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
