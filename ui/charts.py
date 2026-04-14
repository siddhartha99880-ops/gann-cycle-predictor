"""
ui/charts.py — Plotly Candlestick Charts with Gann Cycle Phase Overlay
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PHASE_COLORS_PLOTLY, BULLISH_COLOR, BEARISH_COLOR


def create_main_chart(df, cycle_result=None, show_emas=True):
    """Create candlestick chart with EMA overlays, volume, and RSI subplots."""
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark", title="No data available")
        return fig

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("", "Volume", "RSI"),
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color=BULLISH_COLOR,
        decreasing_line_color=BEARISH_COLOR,
        increasing_fillcolor=BULLISH_COLOR,
        decreasing_fillcolor=BEARISH_COLOR,
        name="Price", showlegend=False,
    ), row=1, col=1)

    # EMA overlays
    if show_emas:
        ema_colors = {"EMA_9": "#ffeb3b", "EMA_20": "#2196f3",
                      "EMA_50": "#ff9800", "EMA_200": "#e91e63"}
        for col, color in ema_colors.items():
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[col], mode="lines",
                    line=dict(color=color, width=1),
                    name=col, opacity=0.8,
                ), row=1, col=1)

    # Phase background overlay
    if cycle_result and cycle_result.get("phase"):
        phase = cycle_result["phase"]
        bg_color = cycle_result.get("bg_color", "rgba(100,100,100,0.05)")
        fig.add_vrect(
            x0=df.index[-min(cycle_result.get("duration", 5), len(df))],
            x1=df.index[-1], fillcolor=bg_color,
            layer="below", line_width=0, row=1, col=1,
        )

    # Volume bars
    if "Volume" in df.columns:
        colors = [BULLISH_COLOR if df["Close"].iloc[i] >= df["Open"].iloc[i]
                  else BEARISH_COLOR for i in range(len(df))]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"], marker_color=colors,
            opacity=0.5, name="Volume", showlegend=False,
        ), row=2, col=1)

    # RSI
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["RSI"], mode="lines",
            line=dict(color="#ab47bc", width=1.5), name="RSI",
        ), row=3, col=1)
        # RSI levels
        for level, color in [(70, "rgba(231,76,60,0.3)"), (30, "rgba(46,204,113,0.3)"),
                              (50, "rgba(255,255,255,0.15)")]:
            fig.add_hline(y=level, line_dash="dot",
                         line_color=color, row=3, col=1)

    fig.update_layout(
        template="plotly_dark",
        height=700, margin=dict(l=50, r=20, t=30, b=30),
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#e0e0e0", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis3=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
    )
    for i in range(1, 4):
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", row=i, col=1)

    return fig


def create_mini_chart(df, height=200):
    """Create a small sparkline-style price chart."""
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark", height=height)
        return fig

    color = BULLISH_COLOR if df["Close"].iloc[-1] >= df["Close"].iloc[0] else BEARISH_COLOR
    fig = go.Figure(go.Scatter(
        x=df.index, y=df["Close"], mode="lines",
        line=dict(color=color, width=1.5), fill="tozeroy",
        fillcolor=color.replace(")", ",0.1)").replace("rgb", "rgba") if "rgb" in color else f"rgba(0,212,170,0.1)",
    ))
    fig.update_layout(
        template="plotly_dark", height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
