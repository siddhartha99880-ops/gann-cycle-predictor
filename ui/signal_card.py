"""
ui/signal_card.py — Signal Card Component
Renders the prediction signal as a styled Streamlit card.
"""
import streamlit as st


def render_signal_card(prediction):
    """Render the main prediction signal card."""
    bias = prediction.get("directional_bias", "SIDEWAYS")
    strength = prediction.get("signal_strength", "WEAK")
    confidence = prediction.get("composite_confidence", prediction.get("phase_confidence", 0))
    phase_name = prediction.get("phase_name", "Unknown")
    phase = prediction.get("gann_cycle_phase", 0)

    # Colors
    bias_colors = {"BULLISH": "#00d4aa", "BEARISH": "#e74c3c", "SIDEWAYS": "#f39c12"}
    strength_colors = {"STRONG": "#00d4aa", "MODERATE": "#f39c12", "WEAK": "#e74c3c"}
    bc = bias_colors.get(bias, "#888")
    sc = strength_colors.get(strength, "#888")

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1f2e 0%, #0e1117 100%);
                border: 1px solid {bc}40; border-radius: 16px; padding: 24px;
                box-shadow: 0 4px 20px {bc}15;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
            <div>
                <span style="font-size:32px; font-weight:700; color:{bc};">{bias}</span>
                <span style="background:{sc}20; color:{sc}; padding:4px 12px; border-radius:20px;
                       font-size:12px; font-weight:600; margin-left:12px;">{strength}</span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:36px; font-weight:700; color:{bc};">{confidence:.0f}%</div>
                <div style="font-size:11px; color:#888;">Composite Confidence</div>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-top:16px;">
            <div style="background:#0e111720; padding:12px; border-radius:10px; border:1px solid #2d354830;">
                <div style="font-size:10px; color:#888; text-transform:uppercase;">Phase</div>
                <div style="font-size:16px; font-weight:600; color:#e0e0e0;">{phase_name}</div>
                <div style="font-size:11px; color:#666;">Phase {phase} of 6</div>
            </div>
            <div style="background:#0e111720; padding:12px; border-radius:10px; border:1px solid #2d354830;">
                <div style="font-size:10px; color:#888; text-transform:uppercase;">Duration</div>
                <div style="font-size:16px; font-weight:600; color:#e0e0e0;">{prediction.get('phase_duration_bars', 0)} bars</div>
                <div style="font-size:11px; color:#666;">In current phase</div>
            </div>
            <div style="background:#0e111720; padding:12px; border-radius:10px; border:1px solid #2d354830;">
                <div style="font-size:10px; color:#888; text-transform:uppercase;">Next Phase</div>
                <div style="font-size:16px; font-weight:600; color:#e0e0e0;">{prediction.get('next_phase_predicted', 'N/A')}</div>
                <div style="font-size:11px; color:#666;">Predicted next</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_levels_card(prediction):
    """Render entry/exit levels card."""
    entry = prediction.get("entry_zone", [])
    targets = prediction.get("targets", [])
    sl = prediction.get("stop_loss", 0)
    rr = prediction.get("risk_reward", "N/A")
    bias = prediction.get("directional_bias", "SIDEWAYS")
    bc = "#00d4aa" if bias == "BULLISH" else ("#e74c3c" if bias == "BEARISH" else "#f39c12")

    entry_str = f"₹{entry[0]:,.1f} — ₹{entry[1]:,.1f}" if len(entry) == 2 else "N/A"
    t_strs = [f"₹{t:,.1f}" for t in targets] if targets else ["N/A"]

    st.markdown(f"""
    <div style="background:#1a1f2e; border:1px solid #2d3548; border-radius:12px; padding:20px;">
        <h4 style="color:#e0e0e0; margin:0 0 16px 0; font-size:14px;">📊 Entry / Exit Levels</h4>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
            <div style="padding:10px; background:#0e111780; border-radius:8px;">
                <div style="font-size:10px; color:#888;">ENTRY ZONE</div>
                <div style="font-size:14px; color:{bc}; font-weight:600;">{entry_str}</div>
            </div>
            <div style="padding:10px; background:#0e111780; border-radius:8px;">
                <div style="font-size:10px; color:#888;">STOP LOSS</div>
                <div style="font-size:14px; color:#e74c3c; font-weight:600;">₹{sl:,.1f}</div>
            </div>
            <div style="padding:10px; background:#0e111780; border-radius:8px;">
                <div style="font-size:10px; color:#888;">TARGETS</div>
                <div style="font-size:13px; color:#00d4aa;">{'  →  '.join(t_strs)}</div>
            </div>
            <div style="padding:10px; background:#0e111780; border-radius:8px;">
                <div style="font-size:10px; color:#888;">RISK : REWARD</div>
                <div style="font-size:14px; color:#f39c12; font-weight:600;">{rr}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_market_data_card(prediction):
    """Render PCR, VIX, OI, FII/DII data card."""
    pcr = prediction.get("pcr", 0)
    vix = prediction.get("india_vix", 0)
    oi = prediction.get("oi_signal", "N/A")
    fii = prediction.get("fii_activity", "N/A")
    dii = prediction.get("dii_activity", "N/A")
    opts = prediction.get("options_suggestion", "N/A")

    vix_color = "#e74c3c" if vix > 20 else ("#f39c12" if vix > 15 else "#00d4aa")

    st.markdown(f"""
    <div style="background:#1a1f2e; border:1px solid #2d3548; border-radius:12px; padding:20px;">
        <h4 style="color:#e0e0e0; margin:0 0 16px 0; font-size:14px;">🏛️ Market Sentiment</h4>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px;">
            <div style="padding:10px; background:#0e111780; border-radius:8px; text-align:center;">
                <div style="font-size:10px; color:#888;">PCR</div>
                <div style="font-size:18px; font-weight:700; color:#2196f3;">{pcr:.2f}</div>
            </div>
            <div style="padding:10px; background:#0e111780; border-radius:8px; text-align:center;">
                <div style="font-size:10px; color:#888;">INDIA VIX</div>
                <div style="font-size:18px; font-weight:700; color:{vix_color};">{vix:.1f}</div>
            </div>
            <div style="padding:10px; background:#0e111780; border-radius:8px; text-align:center;">
                <div style="font-size:10px; color:#888;">OI SIGNAL</div>
                <div style="font-size:12px; font-weight:600; color:#e0e0e0;">{oi}</div>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px;">
            <div style="padding:10px; background:#0e111780; border-radius:8px;">
                <div style="font-size:10px; color:#888;">FII Activity</div>
                <div style="font-size:13px; color:{'#00d4aa' if 'Buyer' in fii else '#e74c3c'};">{fii}</div>
            </div>
            <div style="padding:10px; background:#0e111780; border-radius:8px;">
                <div style="font-size:10px; color:#888;">DII Activity</div>
                <div style="font-size:13px; color:{'#00d4aa' if 'Buyer' in dii else '#e74c3c'};">{dii}</div>
            </div>
        </div>
        <div style="margin-top:12px; padding:10px; background:#0e111780; border-radius:8px; border-left:3px solid #f39c12;">
            <div style="font-size:10px; color:#888;">OPTIONS STRATEGY</div>
            <div style="font-size:13px; color:#f39c12; font-weight:600;">{opts}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
