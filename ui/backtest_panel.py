"""
ui/backtest_panel.py — Backtest Results Display
Renders backtest metrics, equity curve, and trade log.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def render_backtest_results(result):
    """Render complete backtest results panel."""
    if not result or result.get("total_trades", 0) == 0:
        st.warning("No trades generated during backtest period. Try a longer date range.")
        return

    # Metrics row
    cols = st.columns(4)
    metrics = [
        ("Total Trades", result["total_trades"], ""),
        ("Win Rate", f"{result['win_rate']:.1f}", "%"),
        ("Avg Return", f"{result['avg_return']:.2f}", "%"),
        ("Total Return", f"{result['total_return']:.2f}", "%"),
    ]
    for col, (label, val, suffix) in zip(cols, metrics):
        col.metric(label, f"{val}{suffix}")

    cols2 = st.columns(4)
    metrics2 = [
        ("Winning Trades", result.get("winning_trades", 0), ""),
        ("Losing Trades", result.get("losing_trades", 0), ""),
        ("Max Drawdown", f"{result['max_drawdown']:.2f}", "%"),
        ("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}", ""),
    ]
    for col, (label, val, suffix) in zip(cols2, metrics2):
        col.metric(label, f"{val}{suffix}")

    st.markdown("---")

    # Equity curve
    equity = result.get("equity_curve", [])
    if equity and len(equity) > 1:
        st.subheader("📈 Equity Curve")
        fig = go.Figure(go.Scatter(
            y=equity, mode="lines",
            line=dict(color="#00d4aa", width=2),
            fill="tozeroy", fillcolor="rgba(0,212,170,0.08)",
        ))
        fig.update_layout(
            template="plotly_dark", height=300,
            margin=dict(l=50, r=20, t=10, b=30),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(title="Portfolio Value (₹)", gridcolor="rgba(255,255,255,0.05)"),
            xaxis=dict(title="Bars", gridcolor="rgba(255,255,255,0.05)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Trade log
    trades = result.get("trade_log", [])
    if trades:
        st.subheader("📋 Trade Log")
        trade_df = pd.DataFrame(trades)
        trade_df["pnl_color"] = trade_df["pnl_pct"].apply(
            lambda x: "🟢" if x > 0 else "🔴"
        )

        st.dataframe(
            trade_df[["pnl_color", "type", "entry_date", "exit_date",
                      "entry_price", "exit_price", "pnl_pct", "bars_held"]].rename(
                columns={"pnl_color": "", "type": "Type", "entry_date": "Entry",
                         "exit_date": "Exit", "entry_price": "Entry ₹",
                         "exit_price": "Exit ₹", "pnl_pct": "P&L %",
                         "bars_held": "Bars"}
            ),
            use_container_width=True, height=300,
        )
