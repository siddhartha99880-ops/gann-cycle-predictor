export default function Sidebar({ tabs, activeTab, onTabChange, symbols, selectedSymbol, onSymbolChange, selectedTF, onTFChange }) {
  const timeframes = [
    { value: '5m', label: '5 Min' },
    { value: '15m', label: '15 Min' },
    { value: '1h', label: '1 Hour' },
    { value: '1d', label: 'Daily' },
    { value: '1wk', label: 'Weekly' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">G</div>
        <div>
          <div className="brand-text">Gann Cycle</div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 500, letterSpacing: '0.04em' }}>
            MARKET INTELLIGENCE
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {tabs.map(tab => (
          <div
            key={tab.id}
            className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <span style={{ fontSize: '1rem', opacity: 0.7, width: 20, textAlign: 'center' }}>{tab.icon}</span>
            <span>{tab.label}</span>
            {tab.id === 'alerts' && (
              <span className="live-dot" style={{ marginLeft: 'auto' }} />
            )}
          </div>
        ))}
      </nav>

      <div className="sidebar-controls" style={{
        padding: '20px 16px',
        borderTop: '1px solid var(--border-default)',
        marginTop: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px'
      }}>
        <div className="control-group">
          <label className="control-label">Symbol</label>
          <select className="control-select" value={selectedSymbol} onChange={e => onSymbolChange(e.target.value)}>
            {symbols.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="control-group">
          <label className="control-label">Timeframe</label>
          <select className="control-select" value={selectedTF} onChange={e => onTFChange(e.target.value)}>
            {timeframes.map(tf => <option key={tf.value} value={tf.value}>{tf.label}</option>)}
          </select>
        </div>

        {/* Version badge */}
        <div style={{
          marginTop: 8,
          padding: '10px 14px',
          borderRadius: 'var(--radius-sm)',
          background: 'rgba(99, 131, 255, 0.04)',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.68rem',
          color: 'var(--text-muted)',
          textAlign: 'center',
          letterSpacing: '0.04em',
        }}>
          Gann Engine v2.0 · Square of 9
        </div>
      </div>
    </aside>
  );
}
