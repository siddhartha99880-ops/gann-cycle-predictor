/**
 * app.js — Gann Cycle Predictor Frontend
 * API client + Plotly charts + Tab management + UI logic
 */

// ════════════════════════════════════════════
// CONFIG
// ════════════════════════════════════════════
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://gann-backend-api.up.railway.app';

const PHASE_COLORS = {
    '1': '#2ecc71', '2': '#27ae60', '3': '#00d4aa',
    '4': '#f39c12', '5': '#e74c3c', '6': '#c0392b',
};
const BIAS_COLORS = { BULLISH: '#00d4aa', BEARISH: '#e74c3c', SIDEWAYS: '#f39c12' };
const PLOTLY_LAYOUT_BASE = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(26,31,46,0.8)',
    font: { family: 'Inter, sans-serif', color: '#e0e0e0', size: 11 },
    margin: { l: 50, r: 20, t: 30, b: 40 },
    xaxis: { gridcolor: '#2d3548', zerolinecolor: '#2d3548' },
    yaxis: { gridcolor: '#2d3548', zerolinecolor: '#2d3548' },
};
const PLOTLY_CONFIG = { displayModeBar: true, displaylogo: false, responsive: true };

let currentSymbol = 'NIFTY 50';
let currentTimeframe = '1d';
let symbolList = [];
let timeframeMap = {};

// ════════════════════════════════════════════
// API CLIENT
// ════════════════════════════════════════════
async function api(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    try {
        const resp = await fetch(url, {
            ...options,
            headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
        });
        if (!resp.ok) throw new Error(`API ${resp.status}: ${resp.statusText}`);
        return await resp.json();
    } catch (err) {
        console.error(`API Error [${endpoint}]:`, err);
        throw err;
    }
}

// ════════════════════════════════════════════
// INITIALIZATION
// ════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', async () => {
    setupTabs();
    setupMobileMenu();
    setupEventListeners();
    await loadSymbols();
    loadDashboard();
});

async function loadSymbols() {
    try {
        const data = await api('/api/symbols');
        symbolList = data.symbols || [];
        timeframeMap = data.timeframes || {};

        const symSel = document.getElementById('symbol-select');
        const btSym = document.getElementById('bt-symbol');
        symbolList.forEach(s => {
            symSel.add(new Option(s, s));
            btSym.add(new Option(s, s));
        });
        symSel.value = currentSymbol;

        const tfSel = document.getElementById('timeframe-select');
        Object.entries(timeframeMap).forEach(([key, label]) => {
            tfSel.add(new Option(label, key));
        });
        tfSel.value = currentTimeframe;

        // Backtest defaults
        const today = new Date();
        const twoYearsAgo = new Date(today.getFullYear() - 2, today.getMonth(), today.getDate());
        document.getElementById('bt-end').value = today.toISOString().split('T')[0];
        document.getElementById('bt-start').value = twoYearsAgo.toISOString().split('T')[0];
    } catch (e) {
        console.warn('Could not load symbols, using defaults');
    }
}

// ════════════════════════════════════════════
// EVENT LISTENERS
// ════════════════════════════════════════════
function setupEventListeners() {
    document.getElementById('symbol-select').addEventListener('change', (e) => {
        currentSymbol = e.target.value;
        loadDashboard();
    });
    document.getElementById('timeframe-select').addEventListener('change', (e) => {
        currentTimeframe = e.target.value;
        loadDashboard();
    });
    document.getElementById('refresh-btn').addEventListener('click', () => loadDashboard());
    document.getElementById('bt-run').addEventListener('click', () => runBacktest());
}

// ════════════════════════════════════════════
// TAB NAVIGATION
// ════════════════════════════════════════════
function setupTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const panel = document.getElementById(`panel-${tab.dataset.tab}`);
            if (panel) panel.classList.add('active');

            // Lazy load tab data
            const tabName = tab.dataset.tab;
            if (tabName === 'mtf') loadMTF();
            else if (tabName === 'heatmap') loadHeatmap();
            else if (tabName === 'alerts') loadAlerts();
        });
    });
}

// ════════════════════════════════════════════
// MOBILE MENU
// ════════════════════════════════════════════
function setupMobileMenu() {
    const toggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    toggle?.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
    });
    overlay?.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
    });
}

// ════════════════════════════════════════════
// DASHBOARD
// ════════════════════════════════════════════
async function loadDashboard() {
    showLoading(true);
    try {
        const data = await api(`/api/prediction?symbol=${encodeURIComponent(currentSymbol)}&timeframe=${currentTimeframe}`);
        renderDashboard(data);
    } catch (err) {
        showLoading(false);
        showToast(`Failed to load data: ${err.message}`, 'critical');
    }
}

function renderDashboard(data) {
    showLoading(false);
    updateTimestamp();

    // Show alerts
    const toastContainer = document.getElementById('alert-toast-container');
    toastContainer.innerHTML = '';
    (data.alerts || []).forEach(a => {
        const sev = a.severity === 'CRITICAL' ? 'critical' : (a.severity === 'WARNING' ? 'warning' : 'info');
        showToast(a.message, sev);
    });

    // Metrics
    setText('mv-price', `₹${num(data.price)}`);
    const priceD = document.getElementById('md-price');
    priceD.textContent = `${data.price_change_pct >= 0 ? '+' : ''}${num(data.price_change_pct)}%`;
    priceD.className = `metric-delta ${data.price_change_pct >= 0 ? 'up' : 'down'}`;

    setText('mv-phase', data.phase_name || '—');
    const phaseD = document.getElementById('md-phase');
    phaseD.textContent = `Phase ${data.gann_cycle_phase}`;
    phaseD.className = 'metric-delta up';

    setText('mv-confidence', `${num(data.composite_confidence)}%`);
    setText('mv-vix', num(data.india_vix));
    setText('mv-pcr', num(data.pcr, 2));

    // Signal card
    const sc = data.signal_card || {};
    const biasEl = document.getElementById('signal-bias');
    biasEl.textContent = data.directional_bias || '—';
    biasEl.style.color = BIAS_COLORS[data.directional_bias] || '#888';

    const strengthBadge = document.getElementById('signal-strength');
    strengthBadge.textContent = sc.signal_strength || '—';
    const strColor = sc.signal_strength === 'STRONG' ? '#00d4aa' : (sc.signal_strength === 'MODERATE' ? '#f39c12' : '#e74c3c');
    strengthBadge.style.background = strColor + '20';
    strengthBadge.style.color = strColor;
    strengthBadge.style.border = `1px solid ${strColor}40`;

    setText('signal-confidence', `${num(data.composite_confidence)}%`);
    setText('sig-phase', `${data.phase_name} — Phase ${data.gann_cycle_phase} of 6`);
    setText('sig-duration', `${data.phase_duration_bars} bars`);
    setText('sig-next', data.next_phase_predicted || '—');
    setText('sig-entry', sc.entry_zone_str || '—');
    setText('sig-targets', (sc.targets_str || []).join(' → '));
    setText('sig-sl', sc.stop_loss_str || '—');
    setText('sig-rr', sc.risk_reward || '—');

    // Levels
    setText('lv-support', `₹${num(data.support)}`);
    setText('lv-resistance', `₹${num(data.resistance)}`);
    setText('lv-upper', `₹${num(data.upper_band)}`);
    setText('lv-lower', `₹${num(data.lower_band)}`);

    // Market data
    setText('mk-oi', data.oi_signal || '—');
    setText('mk-fii', data.fii_activity || '—');
    setText('mk-dii', data.dii_activity || '—');
    setText('mk-options', data.options_suggestion || '—');

    // Charts
    renderMainChart(data.ohlcv || []);
    renderPhaseGauge(data.gann_cycle_phase, data.composite_confidence, data.phase_name);
    renderPhaseScores(data.phase_scores || {});
}

// ════════════════════════════════════════════
// CHARTS
// ════════════════════════════════════════════
function renderMainChart(ohlcv) {
    if (!ohlcv.length) return;

    const dates = ohlcv.map(d => d.date);
    const traces = [
        {
            type: 'candlestick', x: dates,
            open: ohlcv.map(d => d.open), high: ohlcv.map(d => d.high),
            low: ohlcv.map(d => d.low), close: ohlcv.map(d => d.close),
            increasing: { line: { color: '#00d4aa' }, fillcolor: 'rgba(0,212,170,0.3)' },
            decreasing: { line: { color: '#e74c3c' }, fillcolor: 'rgba(231,76,60,0.3)' },
            name: 'Price',
        },
    ];

    // EMAs
    const emaConfigs = [
        { key: 'ema_9', color: '#ff6b6b', name: 'EMA 9' },
        { key: 'ema_20', color: '#feca57', name: 'EMA 20' },
        { key: 'ema_50', color: '#48dbfb', name: 'EMA 50' },
        { key: 'ema_200', color: '#ff9ff3', name: 'EMA 200' },
    ];
    emaConfigs.forEach(({ key, color, name }) => {
        const vals = ohlcv.map(d => d[key]).filter(v => v != null);
        if (vals.length > 10) {
            traces.push({
                type: 'scatter', mode: 'lines', x: dates.slice(-vals.length),
                y: vals, name, line: { color, width: 1.2 },
            });
        }
    });

    const layout = {
        ...PLOTLY_LAYOUT_BASE,
        title: { text: `${currentSymbol} — ${timeframeMap[currentTimeframe] || currentTimeframe}`, font: { size: 14 } },
        xaxis: { ...PLOTLY_LAYOUT_BASE.xaxis, rangeslider: { visible: false } },
        yaxis: { ...PLOTLY_LAYOUT_BASE.yaxis, title: 'Price (₹)' },
        legend: { orientation: 'h', y: 1.12, font: { size: 10 } },
        height: 420,
    };

    Plotly.newPlot('main-chart', traces, layout, PLOTLY_CONFIG);
}

function renderPhaseGauge(phase, confidence, phaseName) {
    const color = PHASE_COLORS[String(phase)] || '#888';
    const data = [{
        type: 'indicator', mode: 'gauge+number',
        value: phase,
        title: { text: phaseName || 'Phase', font: { size: 13, color: '#e0e0e0' } },
        number: { font: { size: 28, color } },
        gauge: {
            axis: { range: [0, 7], tickvals: [1,2,3,4,5,6], ticktext: ['Acc','MkB','MkA','Dis','MdB','Cap'], tickfont: { size: 9, color: '#888' } },
            bar: { color, thickness: 0.8 },
            bgcolor: '#1a1f2e',
            bordercolor: '#2d3548',
            steps: [
                { range: [0,3.5], color: 'rgba(0,212,170,0.08)' },
                { range: [3.5,7], color: 'rgba(231,76,60,0.08)' },
            ],
        },
    }];
    const layout = { ...PLOTLY_LAYOUT_BASE, margin: { l: 20, r: 20, t: 40, b: 10 }, height: 200 };
    Plotly.newPlot('phase-gauge', data, layout, { ...PLOTLY_CONFIG, displayModeBar: false });
}

function renderPhaseScores(scores) {
    const phases = Object.keys(scores);
    if (!phases.length) return;

    const colors = phases.map(p => PHASE_COLORS[p] || '#888');
    const data = [{
        type: 'bar', x: phases.map(p => `P${p}`),
        y: phases.map(p => scores[p]),
        marker: { color: colors, opacity: 0.8, line: { color: colors, width: 1 } },
    }];
    const layout = {
        ...PLOTLY_LAYOUT_BASE,
        margin: { l: 30, r: 10, t: 20, b: 30 },
        height: 200,
        xaxis: { ...PLOTLY_LAYOUT_BASE.xaxis, title: '' },
        yaxis: { ...PLOTLY_LAYOUT_BASE.yaxis, title: 'Score' },
        showlegend: false,
    };
    Plotly.newPlot('phase-scores-chart', data, layout, { ...PLOTLY_CONFIG, displayModeBar: false });
}

// ════════════════════════════════════════════
// MULTI-TIMEFRAME
// ════════════════════════════════════════════
async function loadMTF() {
    const subtitle = document.getElementById('mtf-subtitle');
    subtitle.textContent = `Analyzing ${currentSymbol} across all timeframes...`;

    try {
        const data = await api(`/api/multi-timeframe?symbol=${encodeURIComponent(currentSymbol)}`);
        renderMTF(data);
    } catch (err) {
        showToast(`MTF analysis failed: ${err.message}`, 'critical');
    }
}

function renderMTF(data) {
    const c = data.confluence || {};
    setText('mtf-bull', `${c.bullish_count || 0}/${c.total || 0}`);
    setText('mtf-bear', `${c.bearish_count || 0}/${c.total || 0}`);
    setText('mtf-align', `${num(c.alignment_score)}%`);
    setText('mtf-strength', c.strength || 'N/A');

    // Table
    const tbody = document.getElementById('mtf-tbody');
    tbody.innerHTML = '';
    const results = data.results || {};
    Object.entries(results).forEach(([tf, res]) => {
        const biasColor = BIAS_COLORS[res.bias] || '#888';
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${res.timeframe_label || tf}</td>
            <td style="color:${res.color || '#888'}">${res.icon || ''} ${res.phase_name} (${res.phase})</td>
            <td>${num(res.confidence)}%</td>
            <td style="color:${biasColor};font-weight:700">${res.bias}</td>
            <td>${res.duration} bars</td>
            <td>${res.next_phase_name || 'N/A'}</td>
        `;
        tbody.appendChild(row);
    });

    // Verdict
    const bias = c.dominant_bias || 'SIDEWAYS';
    const verdictBias = document.getElementById('mtf-verdict-bias');
    verdictBias.textContent = bias;
    verdictBias.style.color = BIAS_COLORS[bias] || '#888';
    setText('mtf-verdict-detail', `${num(c.alignment_score)}% alignment — ${c.strength || 'WEAK'}`);
    document.getElementById('mtf-subtitle').textContent = `Analyzing ${currentSymbol} across all timeframes`;
}

// ════════════════════════════════════════════
// BACKTEST
// ════════════════════════════════════════════
async function runBacktest() {
    const symbol = document.getElementById('bt-symbol').value;
    const start = document.getElementById('bt-start').value;
    const end = document.getElementById('bt-end').value;

    if (!symbol || !start || !end) return showToast('Please fill all fields', 'warning');

    document.getElementById('bt-run').textContent = '⏳ Running...';
    document.getElementById('bt-run').disabled = true;

    try {
        const data = await api('/api/backtest', {
            method: 'POST',
            body: JSON.stringify({ symbol, start_date: start, end_date: end }),
        });
        renderBacktest(data);
    } catch (err) {
        showToast(`Backtest failed: ${err.message}`, 'critical');
    } finally {
        document.getElementById('bt-run').textContent = '▶️ Run Backtest';
        document.getElementById('bt-run').disabled = false;
    }
}

function renderBacktest(data) {
    document.getElementById('bt-results').classList.remove('hidden');

    setText('bt-trades', data.total_trades || 0);
    setText('bt-winrate', `${num(data.win_rate)}%`);
    const retEl = document.getElementById('bt-return');
    retEl.textContent = `${num(data.total_return)}%`;
    retEl.style.color = data.total_return >= 0 ? '#00d4aa' : '#e74c3c';
    setText('bt-drawdown', `${num(data.max_drawdown)}%`);
    setText('bt-sharpe', num(data.sharpe_ratio));

    // Equity curve
    const eq = data.equity_curve || [];
    if (eq.length > 1) {
        const trace = {
            type: 'scatter', mode: 'lines',
            y: eq, x: Array.from({ length: eq.length }, (_, i) => i),
            line: { color: '#00d4aa', width: 2 },
            fill: 'tozeroy', fillcolor: 'rgba(0,212,170,0.08)',
        };
        const layout = {
            ...PLOTLY_LAYOUT_BASE,
            title: { text: 'Equity Curve', font: { size: 14 } },
            yaxis: { ...PLOTLY_LAYOUT_BASE.yaxis, title: 'Portfolio Value (₹)' },
            xaxis: { ...PLOTLY_LAYOUT_BASE.xaxis, title: 'Trade #' },
            height: 360, showlegend: false,
        };
        Plotly.newPlot('bt-equity-chart', [trace], layout, PLOTLY_CONFIG);
    }

    // Trade log
    const tbody = document.getElementById('bt-trade-tbody');
    tbody.innerHTML = '';
    (data.trade_log || []).forEach(t => {
        const color = t.pnl_pct >= 0 ? '#00d4aa' : '#e74c3c';
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="color:${t.type==='LONG'?'#00d4aa':'#e74c3c'};font-weight:700">${t.type}</td>
            <td>${t.entry_date}</td>
            <td>${t.exit_date}</td>
            <td>₹${num(t.entry_price)}</td>
            <td>₹${num(t.exit_price)}</td>
            <td style="color:${color};font-weight:600">${t.pnl_pct >= 0 ? '+' : ''}${num(t.pnl_pct)}%</td>
            <td>${t.bars_held}</td>
        `;
        tbody.appendChild(row);
    });
}

// ════════════════════════════════════════════
// HEATMAP
// ════════════════════════════════════════════
async function loadHeatmap() {
    try {
        const data = await api('/api/heatmap');
        renderHeatmap(data);
    } catch (err) {
        showToast(`Heatmap failed: ${err.message}`, 'critical');
    }
}

function renderHeatmap(data) {
    const grid = document.getElementById('heatmap-grid');
    grid.innerHTML = '';

    const indices = data.indices || {};
    Object.entries(indices).forEach(([name, info]) => {
        const tile = document.createElement('div');
        tile.className = 'heatmap-tile';
        tile.style.setProperty('--tile-color', info.color || '#888');
        tile.innerHTML = `
            <div class="tile-index">${name}</div>
            <div class="tile-phase" style="color:${info.color || '#888'}">${info.icon || ''} ${info.phase_name} (Phase ${info.phase})</div>
            <div class="tile-meta">${info.bias} — ${info.duration} bars → ${info.next_phase_name || 'N/A'}</div>
            <div class="tile-confidence">Confidence: ${num(info.confidence)}%</div>
        `;
        grid.appendChild(tile);
    });

    // Phase distribution chart
    const dist = data.phase_distribution || {};
    const phases = Object.keys(dist);
    if (phases.length) {
        const phaseNames = { '1': 'Accumulation', '2': 'Markup Begin', '3': 'Markup Acceleration', '4': 'Distribution', '5': 'Markdown Begin', '6': 'Capitulation' };
        const trace = {
            type: 'bar',
            x: phases.map(p => phaseNames[p] || `Phase ${p}`),
            y: phases.map(p => dist[p]),
            marker: { color: phases.map(p => PHASE_COLORS[p] || '#888') },
        };
        const layout = {
            ...PLOTLY_LAYOUT_BASE,
            title: { text: 'Phase Distribution Across Indices', font: { size: 14 } },
            height: 360, showlegend: false,
        };
        Plotly.newPlot('phase-dist-chart', [trace], layout, PLOTLY_CONFIG);
    }
}

// ════════════════════════════════════════════
// ALERTS
// ════════════════════════════════════════════
async function loadAlerts() {
    try {
        const data = await api('/api/alerts?limit=30');
        renderAlerts(data);
    } catch (err) {
        showToast(`Alerts failed: ${err.message}`, 'critical');
    }
}

function renderAlerts(data) {
    const alerts = data.alerts || [];
    const tbody = document.getElementById('alerts-tbody');
    const empty = document.getElementById('alerts-empty');

    if (!alerts.length) {
        tbody.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    empty.classList.add('hidden');

    tbody.innerHTML = '';
    alerts.forEach(a => {
        const sevColor = a.severity === 'CRITICAL' ? '#e74c3c' : (a.severity === 'WARNING' ? '#f39c12' : '#00d4aa');
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="font-size:11px">${a.timestamp || '—'}</td>
            <td style="font-weight:600">${a.symbol || '—'}</td>
            <td>${a.alert_type || '—'}</td>
            <td style="color:${sevColor};font-weight:700">${a.severity || '—'}</td>
            <td>${a.message || '—'}</td>
        `;
        tbody.appendChild(row);
    });
}

// ════════════════════════════════════════════
// UTILITIES
// ════════════════════════════════════════════
function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function num(v, decimals = 1) {
    if (v == null || isNaN(v)) return '—';
    return Number(v).toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    const dashPanel = document.getElementById('panel-dashboard');
    if (show) {
        overlay.classList.remove('hidden');
        dashPanel.querySelectorAll('.metrics-row, .signal-card, .chart-row, .info-row').forEach(el => el.style.opacity = '0.3');
    } else {
        overlay.classList.add('hidden');
        dashPanel.querySelectorAll('.metrics-row, .signal-card, .chart-row, .info-row').forEach(el => el.style.opacity = '1');
    }
}

function showToast(message, severity = 'info') {
    const container = document.getElementById('alert-toast-container');
    const toast = document.createElement('div');
    toast.className = `alert-toast ${severity}`;
    toast.innerHTML = `<span>${severity === 'critical' ? '🔴' : (severity === 'warning' ? '⚠️' : 'ℹ️')}</span> ${message}`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 15000);
}

function updateTimestamp() {
    const now = new Date();
    const opts = { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' };
    setText('last-updated-time', now.toLocaleDateString('en-IN', opts));
}
