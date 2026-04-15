"""
backtester.py — Historical Backtesting Engine
Tests Gann Cycle signals on historical NSE data and computes performance metrics.

OPTIMIZED: Uses vectorized phase detection instead of per-bar evaluation.
"""
import os, sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RISK_FREE_RATE, PHASES, PHASE_SCORING_RULES, MAX_PHASE_SCORES
from core.data_fetcher import fetch_historical
from core.indicators import calculate_all_indicators


def _vectorized_phase_detection(df: pd.DataFrame) -> pd.Series:
    """
    Detect Gann Cycle phase for ALL bars at once using vectorized operations.
    Returns a Series of phase numbers (1-6) indexed like df.
    """
    n = len(df)
    # Pre-allocate scores array: shape (n, 6) for phases 1-6
    scores = np.zeros((n, 6), dtype=np.float32)

    close = df["Close"].values
    rsi = df["RSI"].values if "RSI" in df.columns else np.full(n, 50.0)
    ema9 = df["EMA_9"].values if "EMA_9" in df.columns else np.full(n, np.nan)
    ema20 = df["EMA_20"].values if "EMA_20" in df.columns else np.full(n, np.nan)
    ema50 = df["EMA_50"].values if "EMA_50" in df.columns else np.full(n, np.nan)
    macd = df["MACD"].values if "MACD" in df.columns else np.full(n, np.nan)
    macd_signal = df["MACD_Signal"].values if "MACD_Signal" in df.columns else np.full(n, np.nan)
    atr = df["ATR"].values if "ATR" in df.columns else np.full(n, np.nan)
    vol_ratio = df["Volume_Ratio"].values if "Volume_Ratio" in df.columns else np.ones(n)

    # Compute all boolean conditions as arrays
    prev_rsi = np.roll(rsi, 1); prev_rsi[0] = 50.0
    prev_macd = np.roll(macd, 1); prev_macd[0] = np.nan
    prev_signal = np.roll(macd_signal, 1); prev_signal[0] = np.nan

    conditions = {}
    conditions["rsi_30_45"] = (rsi >= 30) & (rsi <= 45)
    conditions["rsi_crossing_50_up"] = (prev_rsi < 50) & (rsi >= 50)
    conditions["rsi_60_75"] = (rsi >= 60) & (rsi <= 75)
    conditions["rsi_below_50"] = rsi < 50
    conditions["rsi_below_30"] = rsi < 30
    conditions["price_above_ema20"] = close > ema20
    conditions["price_below_ema20"] = close < ema20
    conditions["price_above_ema50"] = close > ema50

    # Price far below EMAs
    pct_below_20 = np.where(np.isnan(ema20), 0, (ema20 - close) / np.where(ema20 == 0, 1, ema20))
    pct_below_50 = np.where(np.isnan(ema50), 0, (ema50 - close) / np.where(ema50 == 0, 1, ema50))
    conditions["price_far_below_emas"] = (pct_below_20 > 0.03) & (pct_below_50 > 0.03)

    # Volume
    conditions["low_volume"] = vol_ratio < 0.8
    conditions["high_volume"] = vol_ratio > 1.2

    # MACD crosses
    valid_macd = ~(np.isnan(macd) | np.isnan(macd_signal) | np.isnan(prev_macd) | np.isnan(prev_signal))
    conditions["macd_bullish_cross"] = valid_macd & (prev_macd <= prev_signal) & (macd > macd_signal)
    conditions["macd_bearish_cross"] = valid_macd & (prev_macd >= prev_signal) & (macd < macd_signal)

    # EMA alignment
    conditions["ema9_above_ema20"] = ema9 > ema20
    conditions["ema9_below_ema20"] = ema9 < ema20

    # Sideways (ATR < 60% of 20-bar avg) — simplified rolling
    if not np.all(np.isnan(atr)):
        atr_avg = pd.Series(atr).rolling(20, min_periods=1).mean().values
        conditions["sideways_price"] = atr < (atr_avg * 0.6)
    else:
        conditions["sideways_price"] = np.zeros(n, dtype=bool)

    # Price near highs (within top 5% of 20-bar range)
    high_20 = pd.Series(df["High"].values).rolling(20, min_periods=1).max().values
    low_20 = pd.Series(df["Low"].values).rolling(20, min_periods=1).min().values
    range_20 = high_20 - low_20
    conditions["price_near_highs"] = np.where(range_20 > 0, (close - low_20) / range_20 > 0.95, False)

    # RSI divergences (simplified — just False for speed)
    conditions["rsi_divergence_bearish"] = np.zeros(n, dtype=bool)
    conditions["rsi_divergence_bullish"] = np.zeros(n, dtype=bool)

    # Apply scoring rules
    for condition_key, phase_num, weight in PHASE_SCORING_RULES:
        cond_arr = conditions.get(condition_key)
        if cond_arr is not None:
            scores[:, phase_num - 1] += np.where(cond_arr, weight, 0)

    # Find winning phase for each bar
    phases = np.argmax(scores, axis=1) + 1  # +1 because phases are 1-indexed

    return pd.Series(phases, index=df.index)


def run_backtest(symbol, start_date, end_date, timeframe="1d"):
    """
    Backtest Gann Cycle signals on historical data.
    Strategy: Enter LONG on phase 2 (Markup Begin), exit on phase 4+ (Distribution/Markdown/Capitulation).
              Enter SHORT on phase 5 (Markdown Begin), exit on phase 1/2 (Accumulation/Markup).
    Returns BacktestResult dict with metrics + trade log + equity curve.
    """
    df = fetch_historical(symbol, start_date, end_date, timeframe)
    if df.empty or len(df) < 50:
        return _empty_result(symbol, timeframe, start_date, end_date)

    df = calculate_all_indicators(df)
    df = df.iloc[30:].copy()  # Skip warmup period
    df.reset_index(drop=False, inplace=True)

    # Vectorized phase detection — detect all phases at once!
    phases = _vectorized_phase_detection(df)

    trades = []
    equity = [100000.0]  # Start with 1 lakh
    position = None
    entry_price = 0
    entry_date = None
    entry_idx = 0
    entry_eq_idx = 0

    for i in range(1, len(df)):
        phase = int(phases.iloc[i])
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
            else:
                equity.append(equity[-1])

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
            # Mark-to-market equity
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
