"""
app.py — Gann Cycle Predictor: Main Streamlit Dashboard
Indian Stock Market Futures Prediction Engine

Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys, os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SYMBOL_MAP, TIMEFRAMES, PHASES, INDEX_SYMBOLS
from core.predictor import generate_prediction
from core.gann_cycle import run_multi_timeframe, run_single_timeframe
from core.backtester import run_backtest
from core.alerts import run_all_checks
from core.database import save_signal, get_recent_alerts
from core.signals import format_signal_card
from ui.charts import create_main_chart
from ui.phase_meter import create_phase_gauge, create_confidence_bar, create_phase_timeline
from ui.signal_card import render_signal_card, render_levels_card, render_market_data_card
from ui.heatmap import create_sector_heatmap, create_phase_distribution_chart
from ui.backtest_panel import render_backtest_results
from ui.dashboard_layout import render_header, render_alert_toast, styled_metric

# ────────────────────────────────────────
# PAGE CONFIG
# ────────────────────────────────────────
st.set_page_config(
    page_title="Gann Cycle Predictor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0e1117; }
    .block-container { padding-top: 1rem; }
    div[data-testid="stMetric"] {
        background: #1a1f2e; border: 1px solid #2d3548;
        border-radius: 10px; padding: 12px 16px;
    }
    div[data-testid="stMetric"] label { color: #888 !important; font-size: 11px !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #e0e0e0 !important; }
    section[data-testid="stSidebar"] { background-color: #0a0d14; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        background: #1a1f2e; border-radius: 8px 8px 0 0;
        padding: 8px 20px; border: 1px solid #2d3548;
    }
    .stTabs [aria-selected="true"] { background: #00d4aa20; border-color: #00d4aa; }
    div[data-testid="stExpander"] { border-color: #2d3548 !important; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────
# SIDEBAR
# ────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:16px 0;">
        <h2 style="margin:0; background: linear-gradient(135deg, #00d4aa, #2196f3);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   font-size:20px;">⚡ Gann Cycle</h2>
        <p style="color:#666; font-size:11px; margin:4px 0;">Market Intelligence Engine</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Symbol selection
    symbol = st.selectbox("📈 Symbol", list(SYMBOL_MAP.keys()), index=0)

    # Timeframe
    tf_options = {v["label"]: k for k, v in TIMEFRAMES.items()}
    tf_label = st.selectbox("⏱️ Timeframe", list(tf_options.keys()), index=3)
    timeframe = tf_options[tf_label]

    st.markdown("---")

    # Refresh
    if st.button("🔄 Refresh Analysis", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    # Info
    st.markdown("---")
    st.markdown("""
    <div style="padding:12px; background:#1a1f2e; border-radius:10px; border:1px solid #2d3548;">
        <div style="font-size:11px; color:#888; margin-bottom:8px;">GANN CYCLE PHASES</div>
        <div style="font-size:11px; line-height:1.8;">
            🟢 <span style="color:#2ecc71;">1. Accumulation</span><br>
            🚀 <span style="color:#27ae60;">2. Markup Begin</span><br>
            📈 <span style="color:#00d4aa;">3. Markup Acceleration</span><br>
            ⚠️ <span style="color:#f39c12;">4. Distribution</span><br>
            📉 <span style="color:#e74c3c;">5. Markdown Begin</span><br>
            🔴 <span style="color:#c0392b;">6. Capitulation</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────
# MAIN CONTENT
# ────────────────────────────────────────
render_header()

# Session state for tracking phase transitions
if "prev_phase" not in st.session_state:
    st.session_state.prev_phase = {}

# TABS
tab_dash, tab_mtf, tab_backtest, tab_heatmap, tab_alerts = st.tabs([
    "📊 Dashboard", "🔄 Multi-TF Analysis", "📈 Backtest",
    "🗺️ Sector Heatmap", "🔔 Alerts"
])

# ═══════════════════════════════════════
# TAB 1: MAIN DASHBOARD
# ═══════════════════════════════════════
with tab_dash:
    with st.spinner(f"Analyzing {symbol} on {tf_label} timeframe..."):
        prediction = generate_prediction(symbol, timeframe)

    if prediction.get("gann_cycle_phase", 0) == 0:
        st.error("⚠️ Could not fetch data. Check symbol or try again later.")
    else:
        # Check for alerts
        prev_p = st.session_state.prev_phase.get(symbol)
        alerts = run_all_checks(symbol, prev_p, prediction)
        st.session_state.prev_phase[symbol] = prediction["gann_cycle_phase"]

        if alerts:
            render_alert_toast(alerts)

        # Save signal to DB
        try:
            save_pred = {k: v for k, v in prediction.items() if k != "df"}
            save_pred.pop("cycle_result", None)
            save_pred.pop("market_data", None)
            save_pred.pop("confluence", None)
            save_signal(save_pred)
        except Exception:
            pass

        # ── Top metrics row ──
        df = prediction.get("df", pd.DataFrame())
        if not df.empty:
            close = float(df["Close"].iloc[-1])
            prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else close
            change = close - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Price", f"₹{close:,.2f}", f"{change_pct:+.2f}%")
            c2.metric("Phase", prediction["phase_name"],
                      f"Phase {prediction['gann_cycle_phase']}")
            c3.metric("Confidence", f"{prediction.get('composite_confidence', 0):.0f}%")
            c4.metric("VIX", f"{prediction.get('india_vix', 0):.1f}")
            c5.metric("PCR", f"{prediction.get('pcr', 0):.2f}")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Signal Card ──
        render_signal_card(prediction)
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Chart + Phase Meter ──
        col_chart, col_phase = st.columns([3, 1])

        with col_chart:
            cycle_res = prediction.get("cycle_result", {})
            fig = create_main_chart(df, cycle_res)
            st.plotly_chart(fig, use_container_width=True, key="main_chart")

        with col_phase:
            phase = prediction["gann_cycle_phase"]
            conf = prediction.get("composite_confidence", 0)
            fig_gauge = create_phase_gauge(phase, conf, prediction["phase_name"])
            st.plotly_chart(fig_gauge, use_container_width=True, key="phase_gauge")

            # Phase scores
            scores = cycle_res.get("scores", {})
            if scores:
                fig_scores = create_phase_timeline(scores)
                st.plotly_chart(fig_scores, use_container_width=True, key="phase_scores")

        # ── Levels + Market Data ──
        col_levels, col_market = st.columns(2)
        with col_levels:
            render_levels_card(prediction)
        with col_market:
            render_market_data_card(prediction)

# ═══════════════════════════════════════
# TAB 2: MULTI-TIMEFRAME ANALYSIS
# ═══════════════════════════════════════
with tab_mtf:
    st.subheader("🔄 Multi-Timeframe Gann Cycle Analysis")
    st.caption(f"Analyzing {symbol} across all timeframes for confluence signals")

    with st.spinner("Running multi-timeframe analysis..."):
        mtf_data = run_multi_timeframe(symbol)

    results = mtf_data.get("results", {})
    confluence = mtf_data.get("confluence", {})

    if not results:
        st.warning("Could not fetch multi-timeframe data.")
    else:
        # Confluence summary
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Bullish TFs", f"{confluence.get('bullish_count', 0)}/{confluence.get('total', 0)}")
        c2.metric("Bearish TFs", f"{confluence.get('bearish_count', 0)}/{confluence.get('total', 0)}")
        c3.metric("Alignment", f"{confluence.get('alignment_score', 0):.0f}%")
        c4.metric("Strength", confluence.get("strength", "N/A"))

        st.markdown("---")

        # TF results table
        rows = []
        for tf_key, res in results.items():
            tf_label_name = TIMEFRAMES.get(tf_key, {}).get("label", tf_key)
            bias = res.get("bias", "SIDEWAYS")
            color = "#00d4aa" if bias == "BULLISH" else ("#e74c3c" if bias == "BEARISH" else "#f39c12")
            rows.append({
                "Timeframe": tf_label_name,
                "Phase": f"{res.get('phase', 0)} - {res.get('phase_name', 'N/A')}",
                "Confidence": f"{res.get('confidence', 0):.0f}%",
                "Bias": bias,
                "Duration": f"{res.get('duration', 0)} bars",
                "Next Phase": res.get("next_phase_name", "N/A"),
            })

        if rows:
            mtf_df = pd.DataFrame(rows)
            st.dataframe(mtf_df, use_container_width=True, height=250)

        # Confluence visualization
        if confluence.get("total", 0) > 0:
            bias_label = confluence.get("dominant_bias", "SIDEWAYS")
            align = confluence.get("alignment_score", 0)
            st.markdown(f"""
            <div style="background:#1a1f2e; border:1px solid #2d3548; border-radius:12px;
                        padding:20px; text-align:center; margin-top:16px;">
                <div style="font-size:12px; color:#888;">MULTI-TF CONFLUENCE VERDICT</div>
                <div style="font-size:28px; font-weight:700;
                            color:{'#00d4aa' if bias_label=='BULLISH' else ('#e74c3c' if bias_label=='BEARISH' else '#f39c12')};
                            margin:8px 0;">{bias_label}</div>
                <div style="font-size:14px; color:#aaa;">{align:.0f}% alignment — {confluence.get('strength', 'WEAK')}</div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════
# TAB 3: BACKTEST
# ═══════════════════════════════════════
with tab_backtest:
    st.subheader("📈 Gann Cycle Backtest")
    st.caption("Backtest Gann Cycle signals on historical data")

    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        bt_symbol = st.selectbox("Symbol", list(SYMBOL_MAP.keys()),
                                  index=0, key="bt_symbol")
    with bc2:
        bt_start = st.date_input("Start Date",
                                  value=datetime.now() - timedelta(days=730),
                                  key="bt_start")
    with bc3:
        bt_end = st.date_input("End Date", value=datetime.now(), key="bt_end")

    if st.button("▶️ Run Backtest", type="primary", use_container_width=True):
        with st.spinner(f"Backtesting {bt_symbol}..."):
            bt_result = run_backtest(
                bt_symbol,
                bt_start.strftime("%Y-%m-%d"),
                bt_end.strftime("%Y-%m-%d"),
            )
            render_backtest_results(bt_result)

            # Save to DB
            try:
                from core.database import save_backtest_result
                save_bt = {k: v for k, v in bt_result.items()}
                save_backtest_result(save_bt)
            except Exception:
                pass

# ═══════════════════════════════════════
# TAB 4: SECTOR HEATMAP
# ═══════════════════════════════════════
with tab_heatmap:
    st.subheader("🗺️ Index / Sector Gann Cycle Heatmap")
    st.caption("Phase detection across major Indian indices")

    with st.spinner("Analyzing indices..."):
        index_results = {}
        for idx_name in INDEX_SYMBOLS.keys():
            try:
                res = run_single_timeframe(idx_name, "1d")
                if res.get("phase", 0) > 0:
                    index_results[idx_name] = res
            except Exception:
                pass

    if index_results:
        create_sector_heatmap(index_results)
        st.markdown("<br>", unsafe_allow_html=True)

        fig_dist = create_phase_distribution_chart(index_results)
        st.plotly_chart(fig_dist, use_container_width=True, key="phase_dist")
    else:
        st.warning("Could not fetch index data for heatmap.")

# ═══════════════════════════════════════
# TAB 5: ALERTS
# ═══════════════════════════════════════
with tab_alerts:
    st.subheader("🔔 Alert History")
    st.caption("Recent phase transitions, divergences, and risk alerts")

    try:
        recent_alerts = get_recent_alerts(limit=30)
        if recent_alerts:
            alert_df = pd.DataFrame(recent_alerts)
            display_cols = ["timestamp", "symbol", "alert_type", "severity", "message"]
            available_cols = [c for c in display_cols if c in alert_df.columns]
            st.dataframe(alert_df[available_cols], use_container_width=True, height=500)
        else:
            st.info("No alerts yet. Run an analysis to generate alerts.")
    except Exception as e:
        st.error(f"Could not load alerts: {e}")

# ────────────────────────────────────────
# FOOTER
# ────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:16px; color:#555; font-size:11px;">
    ⚡ Gann Cycle Predictor — Built for educational & analysis purposes only.
    Not financial advice. Always do your own research.<br>
    Data sources: Yahoo Finance • NSE India
</div>
""", unsafe_allow_html=True)
