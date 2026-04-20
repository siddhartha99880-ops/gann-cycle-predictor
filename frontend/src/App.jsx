import { useState, useEffect, useCallback } from 'react';
import { api } from './api';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import MultiTF from './components/MultiTF';
import Backtest from './components/Backtest';
import Heatmap from './components/Heatmap';
import Alerts from './components/Alerts';
import './App.css';

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: '◈' },
  { id: 'mtf', label: 'Multi-TF', icon: '◫' },
  { id: 'backtest', label: 'Backtest', icon: '⟐' },
  { id: 'heatmap', label: 'Heatmap', icon: '▦' },
  { id: 'alerts', label: 'Alerts', icon: '◉' },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [symbols, setSymbols] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('NIFTY 50');
  const [selectedTF, setSelectedTF] = useState('1d');
  const [phaseData, setPhaseData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    api.getSymbols().then(data => {
      setSymbols(data.symbols || Object.keys(data));
    }).catch(() => {
      setSymbols(['NIFTY 50','BANK NIFTY','RELIANCE','TCS','HDFCBANK','INFY','ICICIBANK','SBIN']);
    });
  }, []);

  const fetchPhase = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getPhase(selectedSymbol, selectedTF);
      setPhaseData(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Phase fetch failed:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol, selectedTF]);

  useEffect(() => {
    fetchPhase();
  }, [fetchPhase]);

  return (
    <div className="app-container">
      <Sidebar
        tabs={TABS}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        symbols={symbols}
        selectedSymbol={selectedSymbol}
        onSymbolChange={setSelectedSymbol}
        selectedTF={selectedTF}
        onTFChange={setSelectedTF}
      />
      <div className="main-content">
        <Header
          title={TABS.find(t => t.id === activeTab)?.label || 'Dashboard'}
          lastUpdated={lastUpdated}
          onRefresh={fetchPhase}
          loading={loading}
        />
        <div className="page">
          {activeTab === 'dashboard' && (
            <Dashboard data={phaseData} loading={loading} symbol={selectedSymbol} />
          )}
          {activeTab === 'mtf' && (
            <MultiTF symbol={selectedSymbol} />
          )}
          {activeTab === 'backtest' && (
            <Backtest symbols={symbols} />
          )}
          {activeTab === 'heatmap' && (
            <Heatmap />
          )}
          {activeTab === 'alerts' && (
            <Alerts symbol={selectedSymbol} />
          )}
        </div>
      </div>
    </div>
  );
}
