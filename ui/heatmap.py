"""
ui/heatmap.py — Sector & Index Momentum Heatmap
Shows which indices are in which Gann Cycle phase with color coding.
"""
import plotly.graph_objects as go
import streamlit as st
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import INDEX_SYMBOLS, PHASES, PHASE_COLORS_PLOTLY


def create_sector_heatmap(index_results):
    """
    Create a heatmap showing Gann Cycle phase for each index.
    index_results: dict mapping index name to cycle result dict.
    """
    if not index_results:
        st.info("No index data available for heatmap.")
        return

    names = list(index_results.keys())
    phases = [index_results[n].get("phase", 0) for n in names]
    confidences = [index_results[n].get("confidence", 0) for n in names]
    biases = [index_results[n].get("bias", "SIDEWAYS") for n in names]
    phase_names = [index_results[n].get("phase_name", "N/A") for n in names]

    # Build grid data
    cols_html = ""
    for i, name in enumerate(names):
        phase = phases[i]
        conf = confidences[i]
        bias = biases[i]
        p_name = phase_names[i]
        color = PHASE_COLORS_PLOTLY.get(phase, "#888")
        icon = PHASES.get(phase, {}).get("icon", "⚪")

        cols_html += f"""
        <div style="background: linear-gradient(135deg, {color}15, {color}05);
                    border: 1px solid {color}40; border-radius: 12px; padding: 16px;
                    text-align: center; min-width: 140px;">
            <div style="font-size: 24px; margin-bottom: 4px;">{icon}</div>
            <div style="font-size: 13px; font-weight: 700; color: #e0e0e0; margin-bottom: 4px;">{name}</div>
            <div style="font-size: 12px; color: {color}; font-weight: 600;">{p_name}</div>
            <div style="font-size: 11px; color: #888;">Phase {phase} | {conf:.0f}%</div>
            <div style="margin-top: 6px; padding: 3px 8px; border-radius: 10px;
                        background: {color}20; display: inline-block;">
                <span style="font-size: 10px; color: {color}; font-weight: 600;">{bias}</span>
            </div>
        </div>
        """

    st.markdown(f"""
    <div style="display: flex; gap: 12px; flex-wrap: wrap; justify-content: center;">
        {cols_html}
    </div>
    """, unsafe_allow_html=True)


def create_phase_distribution_chart(index_results):
    """Bar chart showing phase distribution across indices."""
    if not index_results:
        return go.Figure()

    names = list(index_results.keys())
    phases = [index_results[n].get("phase", 0) for n in names]
    colors = [PHASE_COLORS_PLOTLY.get(p, "#888") for p in phases]

    fig = go.Figure(go.Bar(
        x=names, y=phases, marker_color=colors,
        text=[PHASES.get(p, {}).get("name", "?")[:6] for p in phases],
        textposition="outside", textfont=dict(size=10),
    ))
    fig.update_layout(
        template="plotly_dark", height=250,
        margin=dict(l=30, r=10, t=10, b=40),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title="Phase", dtick=1, range=[0, 7]),
        xaxis=dict(tickfont=dict(size=10)),
    )
    return fig
