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
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Market Intelligence</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {tabs.map(tab => (
          <div
            key={tab.id}
            className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <span style={{ fontSize: '1rem', opacity: 0.8 }}>{tab.icon}</span>
            <span>{tab.label}</span>
          </div>
        ))}
      </nav>

      <div className="sidebar-controls" style={{ padding: '16px', borderTop: '1px solid var(--border-light)', marginTop: 'auto' }}>
        <div className="control-group" style={{ marginBottom: '12px' }}>
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
      </div>
    </aside>
  );
}
