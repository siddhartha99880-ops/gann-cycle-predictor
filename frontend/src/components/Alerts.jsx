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
        <div className="loading-spinner" style={{ width: 36, height: 36, margin: '0 auto 20px' }} />
        <p>Fetching alerts for <strong style={{ color: 'var(--accent-primary)' }}>{symbol}</strong>…</p>
      </div>
    );
  }

  if (!alerts || alerts.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 20px' }}>
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
          ◉
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: 360, margin: '0 auto', lineHeight: 1.6 }}>
          No alerts generated yet. Run an analysis to trigger phase-change and anomaly alerts.
        </p>
      </div>
    );
  }

  const severityConfig = (sev) => {
    if (sev === 'CRITICAL') return { color: '#dc2626', bg: 'rgba(220, 38, 38, 0.1)', border: 'rgba(220, 38, 38, 0.15)', icon: '🔴' };
    if (sev === 'HIGH') return { color: '#f87171', bg: 'rgba(248, 113, 113, 0.08)', border: 'rgba(248, 113, 113, 0.12)', icon: '🟠' };
    if (sev === 'MEDIUM') return { color: '#fbbf24', bg: 'rgba(251, 191, 36, 0.08)', border: 'rgba(251, 191, 36, 0.12)', icon: '🟡' };
    return { color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.08)', border: 'rgba(56, 189, 248, 0.12)', icon: '🔵' };
  };

  return (
    <div>
      {/* ─── Summary ─── */}
      <div className="grid-cols-4" style={{ marginBottom: 24 }}>
        <div className="metric-card">
          <div className="metric-label">Total Alerts</div>
          <div className="metric-value">{alerts.length}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Critical</div>
          <div className="metric-value text-red">
            {alerts.filter(a => a.severity === 'CRITICAL' || a.severity === 'HIGH').length}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Medium</div>
          <div className="metric-value text-amber">
            {alerts.filter(a => a.severity === 'MEDIUM').length}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Info</div>
          <div className="metric-value text-blue">
            {alerts.filter(a => !a.severity || a.severity === 'LOW' || a.severity === 'INFO').length}
          </div>
        </div>
      </div>

      {/* ─── Alert List ─── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {alerts.map((a, i) => {
          const sev = severityConfig(a.severity);
          return (
            <div
              key={i}
              style={{
                padding: '16px 20px',
                background: 'var(--bg-card)',
                backdropFilter: 'blur(12px)',
                border: `1px solid ${sev.border}`,
                borderRadius: 'var(--radius-md)',
                borderLeft: `3px solid ${sev.color}`,
                display: 'flex',
                alignItems: 'flex-start',
                gap: 14,
                transition: 'all 0.2s ease',
                animation: `fadeInUp 0.3s var(--ease-smooth) ${i * 0.03}s both`,
              }}
            >
              <span style={{ fontSize: '1rem', flexShrink: 0, marginTop: 1 }}>{sev.icon}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4, flexWrap: 'wrap' }}>
                  <span style={{
                    fontWeight: 700,
                    fontSize: '0.82rem',
                    color: 'var(--text-primary)',
                  }}>
                    {a.type || 'Alert'}
                  </span>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: 100,
                    background: sev.bg,
                    border: `1px solid ${sev.border}`,
                    fontSize: '0.62rem',
                    fontWeight: 700,
                    color: sev.color,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}>
                    {a.severity || 'INFO'}
                  </span>
                  <span style={{
                    fontSize: '0.68rem',
                    color: 'var(--text-muted)',
                    fontFamily: "'JetBrains Mono', monospace",
                    marginLeft: 'auto',
                  }}>
                    {a.timestamp || '—'}
                  </span>
                </div>
                <div style={{
                  fontSize: '0.84rem',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.5,
                }}>
                  {a.message || '—'}
                </div>
                {a.symbol && (
                  <div style={{
                    marginTop: 6,
                    fontSize: '0.7rem',
                    color: 'var(--text-muted)',
                    fontWeight: 500,
                  }}>
                    {a.symbol}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
