"""
ui/dashboard_layout.py — Layout helpers for Streamlit dashboard
"""
import streamlit as st
from datetime import datetime


def render_header():
    """Render the dashboard header with title and timestamp."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1f2e 0%, #0e1117 100%);
                padding: 20px 30px; border-radius: 16px; margin-bottom: 20px;
                border: 1px solid #2d354830;
                box-shadow: 0 4px 30px rgba(0,212,170,0.06);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="margin: 0; font-size: 28px; font-weight: 800;
                           background: linear-gradient(135deg, #00d4aa, #2196f3);
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    ⚡ Gann Cycle Predictor
                </h1>
                <p style="margin: 4px 0 0 0; font-size: 13px; color: #888;">
                    Indian Stock Market Futures Prediction Engine
                </p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 11px; color: #666;">Last Updated</div>
                <div style="font-size: 13px; color: #00d4aa; font-weight: 600;">
                    """ + datetime.now().strftime("%d %b %Y, %I:%M %p") + """
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_alert_toast(alerts):
    """Render alerts as Streamlit toasts / notifications."""
    if not alerts:
        return
    for alert in alerts[:5]:  # Show max 5 alerts
        if hasattr(alert, 'severity'):
            sev = alert.severity
            msg = alert.message
        else:
            sev = alert.get("severity", "INFO")
            msg = alert.get("message", "")

        if sev == "CRITICAL":
            st.error(msg, icon="🚨")
        elif sev == "WARNING":
            st.warning(msg, icon="⚠️")
        else:
            st.info(msg, icon="ℹ️")


def styled_metric(label, value, delta=None, color="#e0e0e0"):
    """Render a styled metric card."""
    delta_html = ""
    if delta is not None:
        d_color = "#00d4aa" if delta >= 0 else "#e74c3c"
        d_icon = "▲" if delta >= 0 else "▼"
        delta_html = f'<div style="color:{d_color}; font-size:12px;">{d_icon} {abs(delta):.2f}%</div>'

    st.markdown(f"""
    <div style="background:#1a1f2e; border:1px solid #2d3548; border-radius:10px;
                padding:14px; text-align:center;">
        <div style="font-size:10px; color:#888; text-transform:uppercase; letter-spacing:1px;">{label}</div>
        <div style="font-size:22px; font-weight:700; color:{color}; margin:4px 0;">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)
