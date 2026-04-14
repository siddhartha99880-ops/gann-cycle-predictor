"""
ui/phase_meter.py — Gann Cycle Phase Gauge / Dial
Visual indicator showing current phase (1-6) with color coding.
"""
import plotly.graph_objects as go
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PHASES, PHASE_COLORS_PLOTLY


def create_phase_gauge(phase, confidence, phase_name=""):
    """Create a gauge dial showing current Gann Cycle phase."""
    color = PHASE_COLORS_PLOTLY.get(phase, "#888")
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=phase,
        title={"text": f"<b>{phase_name}</b><br><span style='font-size:12px'>Confidence: {confidence:.0f}%</span>",
               "font": {"size": 16, "color": "#e0e0e0"}},
        number={"font": {"size": 40, "color": color}},
        gauge={
            "axis": {"range": [0.5, 6.5], "tickvals": [1,2,3,4,5,6],
                     "ticktext": ["Acc","MkB","MkA","Dist","MdB","Cap"],
                     "tickfont": {"size": 10, "color": "#aaa"}},
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": "rgba(30,35,50,0.8)",
            "borderwidth": 1, "bordercolor": "#2d3548",
            "steps": [
                {"range": [0.5, 1.5], "color": "rgba(46,204,113,0.15)"},
                {"range": [1.5, 2.5], "color": "rgba(39,174,96,0.15)"},
                {"range": [2.5, 3.5], "color": "rgba(0,212,170,0.15)"},
                {"range": [3.5, 4.5], "color": "rgba(243,156,18,0.15)"},
                {"range": [4.5, 5.5], "color": "rgba(231,76,60,0.15)"},
                {"range": [5.5, 6.5], "color": "rgba(192,57,43,0.15)"},
            ],
            "threshold": {
                "line": {"color": "#fff", "width": 3},
                "thickness": 0.8, "value": phase,
            },
        },
    ))
    fig.update_layout(
        height=250, margin=dict(l=30, r=30, t=60, b=10),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e0"),
    )
    return fig


def create_confidence_bar(confidence, label="Confidence"):
    """Create a horizontal confidence bar."""
    if confidence >= 75:
        color = "#00d4aa"
    elif confidence >= 50:
        color = "#f39c12"
    else:
        color = "#e74c3c"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence,
        number={"suffix": "%", "font": {"size": 28, "color": color}},
        title={"text": label, "font": {"size": 12, "color": "#aaa"}},
        gauge={
            "axis": {"range": [0, 100], "visible": False},
            "bar": {"color": color},
            "bgcolor": "rgba(30,35,50,0.5)",
            "borderwidth": 0,
            "shape": "bullet",
        },
    ))
    fig.update_layout(
        height=80, margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def create_phase_timeline(scores):
    """Create a bar chart showing all 6 phase scores."""
    phases = list(range(1, 7))
    names = [PHASES[p]["name"][:8] for p in phases]
    values = [scores.get(p, 0) for p in phases]
    colors = [PHASE_COLORS_PLOTLY[p] for p in phases]

    fig = go.Figure(go.Bar(x=names, y=values, marker_color=colors, opacity=0.85))
    fig.update_layout(
        template="plotly_dark", height=200,
        margin=dict(l=30, r=10, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickfont=dict(size=9)), yaxis=dict(title="Score", title_font_size=10),
    )
    return fig
