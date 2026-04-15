"""
backtester.py — Historical Backtesting Engine
Tests Gann Cycle signals on historical NSE data and computes performance metrics.
"""
import os, sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RISK_FREE_RATE, PHASES
from core.data_fetcher import fetch_historical
from core.indicators import calculate_all_indicators
from core.gann_cycle import evaluate_conditions, score_phases


def run_backtest(symbol, start_date, end_date, timeframe="1d"):
    """
    Backtest Gann Cycle signals on historical data.
    Strategy: Enter LONG on phase 2 (Markup Begin), exit on phase 4 (Distribution).
              Enter SHORT on phase 5 (Markdown Begin), exit on phase 1 (Accumulation).
    Returns BacktestResult dict with metrics + trade log + equity curve.
    """
    df = fetch_historical(symbol, start_date, end_date, timeframe)
    if df.empty or len(df) < 50:
        return _empty_result(symbol, timeframe, start_date, end_date)

    df = calculate_all_indicators(df)
    df = df.iloc[30:].copy()  # Skip warmup period
    df.reset_index(drop=False, inplace=True)

    trades = []
    equity = [100000.0]  # Start with 1 lakh
    position = None  # None, "LONG", or "SHORT"
    entry_price = 0
    entry_date = None
    entry_idx = 0       # DataFrame row index (for bars_held calc)
    entry_eq_idx = 0    # Equity list index at entry (for mark-to-market)

    for i in range(1, len(df)):
        # Use a fixed lookback window instead of growing slice (massive speedup)
        lookback = min(i + 1, 50)
        row_df = df.iloc[i + 1 - lookback:i + 1].copy()
        if "Date" in row_df.columns:
            row_df.set_index("Date", inplace=True)
        elif "Datetime" in row_df.columns:
            row_df.set_index("Datetime", inplace=True)

        if len(row_df) < 2:
            equity.append(equity[-1])
            continue

        conds = evaluate_conditions(row_df)
        scores = score_phases(conds)
        phase = max(scores, key=scores.get)
        close = float(df["Close"].iloc[i])

        # Entry logic
        if position is None:
            if phase == 2:  # Markup Begin → go LONG
                position = "LONG"
                entry_price = close
                entry_date = df.iloc[i].get("Date", df.index[i] if isinstance(df.index[i], str) else i)
                entry_idx = i
                entry_eq_idx = len(equity) - 1
            elif phase == 5:  # Markdown Begin → go SHORT
                position = "SHORT"
                entry_price = close
                entry_date = df.iloc[i].get("Date", df.index[i] if isinstance(df.index[i], str) else i)
                entry_idx = i
                entry_eq_idx = len(equity) - 1

        # Exit logic
        elif position == "LONG" and phase in [4, 5, 6]:
            pnl_pct = (close - entry_price) / entry_price * 100
            trades.append({
                "type": "LONG",
                "entry_date": str(entry_date),
                "exit_date": str(df.iloc[i].get("Date", i)),
                "entry_price": round(entry_price, 2),
                "exit_price": round(close, 2),
                "pnl_pct": round(pnl_pct, 2),
                "bars_held": i - entry_idx,
            })
            equity.append(equity[-1] * (1 + pnl_pct / 100))
            position = None
        elif position == "SHORT" and phase in [1, 2]:
            pnl_pct = (entry_price - close) / entry_price * 100
            trades.append({
                "type": "SHORT",
                "entry_date": str(entry_date),
                "exit_date": str(df.iloc[i].get("Date", i)),
                "entry_price": round(entry_price, 2),
                "exit_price": round(close, 2),
                "pnl_pct": round(pnl_pct, 2),
                "bars_held": i - entry_idx,
            })
            equity.append(equity[-1] * (1 + pnl_pct / 100))
            position = None
        else:
            # Mark-to-market equity (use entry_eq_idx instead of entry_idx)
            if position == "LONG":
                mtm = (close - entry_price) / entry_price
                equity.append(equity[entry_eq_idx] * (1 + mtm))
            elif position == "SHORT":
                mtm = (entry_price - close) / entry_price
                equity.append(equity[entry_eq_idx] * (1 + mtm))
            else:
                equity.append(equity[-1])

    # Compute metrics
    metrics = _compute_metrics(trades, equity)
    metrics.update({
        "symbol": symbol, "timeframe": timeframe,
        "start_date": start_date, "end_date": end_date,
        "trade_log": trades, "equity_curve": equity,
    })
    return metrics


def _compute_metrics(trades, equity):
    if not trades:
        return {"total_trades":0,"win_rate":0,"avg_return":0,
                "max_drawdown":0,"sharpe_ratio":0,"total_return":0,
                "winning_trades":0,"losing_trades":0}

    pnls = [t["pnl_pct"] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]

    total_return = (equity[-1] / equity[0] - 1) * 100 if equity[0] > 0 else 0

    # Max drawdown
    peak = equity[0]
    max_dd = 0
    for val in equity:
        if val > peak:
            peak = val
        dd = (peak - val) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)

    # Sharpe ratio (annualized)
    if len(pnls) > 1:
        returns_arr = np.array(pnls)
        avg_r = np.mean(returns_arr)
        std_r = np.std(returns_arr)
        sharpe = (avg_r - RISK_FREE_RATE / 252) / std_r * np.sqrt(252) if std_r > 0 else 0
    else:
        sharpe = 0

    return {
        "total_trades": len(trades),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate": round(len(wins)/len(trades)*100, 1) if trades else 0,
        "avg_return": round(np.mean(pnls), 2) if pnls else 0,
        "max_drawdown": round(max_dd, 2),
        "sharpe_ratio": round(sharpe, 2),
        "total_return": round(total_return, 2),
    }


def _empty_result(symbol, timeframe, start, end):
    return {"symbol":symbol,"timeframe":timeframe,"start_date":start,"end_date":end,
            "total_trades":0,"win_rate":0,"avg_return":0,"max_drawdown":0,
            "sharpe_ratio":0,"total_return":0,"winning_trades":0,"losing_trades":0,
            "trade_log":[],"equity_curve":[100000]}
