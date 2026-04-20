export default function Header({ title, lastUpdated, onRefresh, loading }) {
  return (
    <header className="header">
      <div>
        <h1 className="header-title">{title}</h1>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {lastUpdated && (
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Updated {lastUpdated.toLocaleTimeString()}
          </span>
        )}
        <button className="btn btn-primary" onClick={onRefresh} disabled={loading} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {loading && <span className="loading-spinner" />}
          {loading ? 'Analyzing...' : 'Refresh'}
        </button>
      </div>
    </header>
  );
}
