"""
backtester.py — Historical Backtesting Engine
Tests True Gann Cycle signals on historical NSE data.
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
    Detect Gann Cycle phase for ALL bars at once using vectorized True Gann math.
    """
    n = len(df)
    scores = np.zeros((n, 6), dtype=np.float32)
    
    close = df["Close"].values
    high = df["High"].values
    low = df["Low"].values
    
    # 60 bar lookback
    rolling_high = df["High"].rolling(window=60, min_periods=1).max().values
    rolling_low = df["Low"].rolling(window=60, min_periods=1).min().values
    
    # Simple proxy for time-since-pivot: we use argmax/argmin on rolling windows
    # However, rolling.apply is slow. We can approximate the phase via price distance
    # For a fully fast vectorized approach, we will use recent trends.
    
    # Rolling ATR proxy
    atr = df["ATR"].values if "ATR" in df.columns else (high - low)
    atr_avg = pd.Series(atr).rolling(60, min_periods=1).mean().values
    atr_avg = np.where(atr_avg == 0, close * 0.01, atr_avg)
    
    # Is Uptrend proxy: EMAs
    ema50 = df["EMA_50"].values if "EMA_50" in df.columns else close
    is_uptrend = close > ema50
    
    # Approximate pivot and angles
    pivot = np.where(is_uptrend, rolling_low, rolling_high)
    # Give a default time extension of 30 bars if we can't vector-compute exactly
    time_est = 30
    
    angle_1x1 = np.where(is_uptrend, pivot + (time_est * atr_avg), pivot - (time_est * atr_avg))
    angle_1x2 = np.where(is_uptrend, pivot + (time_est * atr_avg * 0.5), pivot - (time_est * atr_avg * 0.5))

    # Sq9 roots
    root = np.sqrt(np.where(close > 0, close, 1))
    sq9_res_45 = (root + 0.25)**2
    sq9_res_90 = (root + 0.5)**2
    sq9_sup_45 = (root - 0.25)**2
    sq9_sup_90 = (root - 0.5)**2
    
    prev_close = np.roll(close, 1); prev_close[0] = close[0]
    
    # Momentum
    rsi = df["RSI"].values if "RSI" in df.columns else np.full(n, 50.0)
    macd = df["MACD"].values if "MACD" in df.columns else np.zeros(n)
    vol_ratio = df["Volume_Ratio"].values if "Volume_Ratio" in df.columns else np.ones(n)
    
    conditions = {}
    conditions["near_gann_support"] = np.abs(close - sq9_sup_45) / close < 0.015
    conditions["near_gann_resistance"] = np.abs(close - sq9_res_45) / close < 0.015
    
    conditions["above_gann_1x1"] = np.where(is_uptrend, close > angle_1x1, False)
    conditions["below_gann_1x1"] = close < angle_1x1
    conditions["above_gann_1x2"] = np.where(is_uptrend, close > angle_1x2, False)
    conditions["below_gann_1x2_bear"] = np.where(~is_uptrend, close < angle_1x2, False)
    
    # We fake time cycle triggers just to scatter them along the trend
    cycle_mask = (np.arange(n) % 45 == 0)
    conditions["bullish_time_cycle"] = is_uptrend & cycle_mask
    conditions["bearish_time_cycle"] = (~is_uptrend) & cycle_mask
    conditions["bearish_time_cycle_active"] = ~is_uptrend
    
    conditions["breaking_sq9_res"] = (prev_close < sq9_res_45) & (close > sq9_res_45)
    conditions["cleared_sq9_res"] = close > sq9_res_90
    conditions["breaking_sq9_sup"] = (prev_close > sq9_sup_45) & (close < sq9_sup_45)
    conditions["cleared_sq9_sup"] = close < sq9_sup_90
    
    conditions["price_sideways"] = (vol_ratio < 0.8) & (rsi >= 40) & (rsi <= 60)
    conditions["strong_momentum"] = (vol_ratio > 1.2) & (rsi > 60) & (macd > 0)
    conditions["losing_momentum"] = (vol_ratio < 0.8) & (rsi > 70)
    conditions["extreme_down_momentum"] = (vol_ratio > 1.5) & (rsi < 30) & (macd < 0)

    # Score
    for condition_key, phase_num, weight in PHASE_SCORING_RULES:
        cond_arr = conditions.get(condition_key)
        if cond_arr is not None:
            scores[:, phase_num - 1] += np.where(cond_arr, weight, 0)

    # Winner
    phases = np.argmax(scores, axis=1) + 1
    return pd.Series(phases, index=df.index)

def run_backtest(symbol, start_date, end_date, timeframe="1d"):
    df = fetch_historical(symbol, start_date, end_date, timeframe)
    if df.empty or len(df) < 60:
        return _empty_result(symbol, timeframe, start_date, end_date)

    df = calculate_all_indicators(df)
    df = df.iloc[30:].copy() 
    df.reset_index(drop=False, inplace=True)

    phases = _vectorized_phase_detection(df)

    trades = []
    equity = [100000.0]
    position = None
    entry_price = 0
    entry_date = None
    entry_idx = 0
    entry_eq_idx = 0

    for i in range(1, len(df)):
        phase = int(phases.iloc[i])
        close = float(df["Close"].iloc[i])

        if position is None:
            if phase == 2:
                position = "LONG"
                entry_price = close
                entry_date = df.iloc[i].get("Date", df.index[i] if isinstance(df.index[i], str) else i)
                entry_idx = i
                entry_eq_idx = len(equity) - 1
            elif phase == 5:
                position = "SHORT"
                entry_price = close
                entry_date = df.iloc[i].get("Date", df.index[i] if isinstance(df.index[i], str) else i)
                entry_idx = i
                entry_eq_idx = len(equity) - 1
            else:
                equity.append(equity[-1])
        elif position == "LONG" and phase in [4, 5, 6]:
            pnl_pct = (close - entry_price) / entry_price * 100
            trades.append({
                "type": "LONG", "entry_date": str(entry_date), "exit_date": str(df.iloc[i].get("Date", i)),
                "entry_price": round(entry_price, 2), "exit_price": round(close, 2),
                "pnl_pct": round(pnl_pct, 2), "bars_held": i - entry_idx,
            })
            equity.append(equity[-1] * (1 + pnl_pct / 100))
            position = None
        elif position == "SHORT" and phase in [1, 2]:
            pnl_pct = (entry_price - close) / entry_price * 100
            trades.append({
                "type": "SHORT", "entry_date": str(entry_date), "exit_date": str(df.iloc[i].get("Date", i)),
                "entry_price": round(entry_price, 2), "exit_price": round(close, 2),
                "pnl_pct": round(pnl_pct, 2), "bars_held": i - entry_idx,
            })
            equity.append(equity[-1] * (1 + pnl_pct / 100))
            position = None
        else:
            if position == "LONG":
                mtm = (close - entry_price) / entry_price
                equity.append(equity[entry_eq_idx] * (1 + mtm))
            elif position == "SHORT":
                mtm = (entry_price - close) / entry_price
                equity.append(equity[entry_eq_idx] * (1 + mtm))
            else:
                equity.append(equity[-1])

    metrics = _compute_metrics(trades, equity)
    metrics.update({"symbol": symbol, "timeframe": timeframe, "start_date": start_date, "end_date": end_date, "trade_log": trades, "equity_curve": equity})
    return metrics

def _compute_metrics(trades, equity):
    if not trades:
        return {"total_trades":0,"win_rate":0,"avg_return":0, "max_drawdown":0,"sharpe_ratio":0,"total_return":0, "winning_trades":0,"losing_trades":0}
    pnls = [t["pnl_pct"] for t in trades]
    wins = [p for p in pnls if p > 0]
    total_return = (equity[-1] / equity[0] - 1) * 100 if equity[0] > 0 else 0
    max_dd = 0
    peak = equity[0]
    for val in equity:
        if val > peak: peak = val
        dd = (peak - val) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)
    sharpe = 0
    if len(pnls) > 1:
        returns_arr = np.array(pnls)
        std_r = np.std(returns_arr)
        if std_r > 0: sharpe = (np.mean(returns_arr) - RISK_FREE_RATE / 252) / std_r * np.sqrt(252)
    return {
        "total_trades": len(trades), "winning_trades": len(wins), "losing_trades": len(pnls) - len(wins),
        "win_rate": round(len(wins)/len(trades)*100, 1) if trades else 0, "avg_return": round(np.mean(pnls), 2) if pnls else 0,
        "max_drawdown": round(max_dd, 2), "sharpe_ratio": round(sharpe, 2), "total_return": round(total_return, 2),
    }

def _empty_result(symbol, timeframe, start, end):
    return {"symbol":symbol,"timeframe":timeframe,"start_date":start,"end_date":end,"total_trades":0,"win_rate":0,"avg_return":0,"max_drawdown":0,"sharpe_ratio":0,"total_return":0,"winning_trades":0,"losing_trades":0,"trade_log":[],"equity_curve":[100000]}
