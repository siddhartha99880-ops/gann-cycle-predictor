export default function Header({ title, lastUpdated, onRefresh, loading }) {
  return (
    <header className="header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <h1 className="header-title">{title}</h1>
        {loading && (
          <div style={{
            padding: '3px 10px',
            borderRadius: 100,
            background: 'rgba(99, 131, 255, 0.08)',
            border: '1px solid rgba(99, 131, 255, 0.12)',
            fontSize: '0.65rem',
            fontWeight: 600,
            color: 'var(--accent-primary)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}>
            <span className="loading-spinner" style={{ width: 10, height: 10, borderWidth: 1.5 }} />
            Processing
          </div>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {lastUpdated && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.76rem',
            color: 'var(--text-muted)',
          }}>
            <span className="live-dot" style={{ width: 6, height: 6 }} />
            <span>Last sync {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
          </div>
        )}
        <button
          className="btn btn-primary"
          onClick={onRefresh}
          disabled={loading}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem' }}
        >
          {loading && <span className="loading-spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />}
          {loading ? 'Analyzing…' : '⟲ Refresh'}
        </button>
      </div>
    </header>
  );
}
