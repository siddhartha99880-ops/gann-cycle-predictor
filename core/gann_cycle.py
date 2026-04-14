"""
gann_cycle.py — ★ CORE ENGINE ★
Gann Cycle Phase Detector — the heart of the prediction system.

Implements W.D. Gann's cyclical market model adapted into 6 phases:
1. Accumulation — Smart money buying quietly
2. Markup Begin — Breakout triggers
3. Markup Acceleration — Strong trending
4. Distribution — Institutional selling
5. Markdown Begin — Breakdown
6. Capitulation — Panic selling

Each phase is scored using weighted technical conditions.
The highest-scoring phase is the detected current phase.
"""

import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PHASES, PHASE_SCORING_RULES, MAX_PHASE_SCORES, TIMEFRAMES
from core.indicators import calculate_all_indicators
from core.data_fetcher import fetch_ohlcv, fetch_multi_timeframe


def evaluate_conditions(df: pd.DataFrame) -> dict:
    """
    Evaluate all market conditions for the latest bar.
    Returns a dict of boolean conditions used for phase scoring.
    """
    if len(df) < 2:
        return {}

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    close = latest["Close"]

    conditions = {}

    # ── RSI Conditions ──
    rsi = latest.get("RSI", 50)
    prev_rsi = prev.get("RSI", 50)
    if pd.notna(rsi):
        conditions["rsi_30_45"] = 30 <= rsi <= 45
        conditions["rsi_crossing_50_up"] = prev_rsi < 50 <= rsi
        conditions["rsi_60_75"] = 60 <= rsi <= 75
        conditions["rsi_below_50"] = rsi < 50
        conditions["rsi_below_30"] = rsi < 30
    else:
        for k in ["rsi_30_45", "rsi_crossing_50_up", "rsi_60_75",
                   "rsi_below_50", "rsi_below_30"]:
            conditions[k] = False

    # ── RSI Divergence ──
    conditions["rsi_divergence_bearish"] = bool(latest.get("RSI_Div_Bearish", False))
    conditions["rsi_divergence_bullish"] = bool(latest.get("RSI_Div_Bullish", False))

    # ── Price vs EMA Conditions ──
    ema20 = latest.get("EMA_20")
    ema50 = latest.get("EMA_50")
    ema200 = latest.get("EMA_200")

    conditions["price_above_ema20"] = (
        close > ema20 if pd.notna(ema20) else False
    )
    conditions["price_below_ema20"] = (
        close < ema20 if pd.notna(ema20) else False
    )
    conditions["price_above_ema50"] = (
        close > ema50 if pd.notna(ema50) else False
    )

    # Price far below EMAs: close is > 3% below both EMA20 and EMA50
    if pd.notna(ema20) and pd.notna(ema50):
        pct_below_20 = (ema20 - close) / ema20
        pct_below_50 = (ema50 - close) / ema50
        conditions["price_far_below_emas"] = (pct_below_20 > 0.03 and pct_below_50 > 0.03)
    else:
        conditions["price_far_below_emas"] = False

    # ── Price Action Conditions ──
    atr = latest.get("ATR")
    if pd.notna(atr) and atr > 0:
        # Sideways: ATR is below 60% of its 20-bar average
        atr_series = df["ATR"].dropna()
        if len(atr_series) >= 20:
            avg_atr = atr_series.tail(20).mean()
            conditions["sideways_price"] = atr < (avg_atr * 0.6)
        else:
            conditions["sideways_price"] = False
    else:
        conditions["sideways_price"] = False

    # Price near recent highs: within top 5% of 20-bar range
    if len(df) >= 20:
        high_20 = df["High"].tail(20).max()
        low_20 = df["Low"].tail(20).min()
        range_20 = high_20 - low_20
        if range_20 > 0:
            conditions["price_near_highs"] = (close - low_20) / range_20 > 0.95
        else:
            conditions["price_near_highs"] = False
    else:
        conditions["price_near_highs"] = False

    # ── Volume Conditions ──
    vol_ratio = latest.get("Volume_Ratio", 1.0)
    if pd.notna(vol_ratio):
        conditions["low_volume"] = vol_ratio < 0.8
        conditions["high_volume"] = vol_ratio > 1.2
    else:
        conditions["low_volume"] = False
        conditions["high_volume"] = False

    # ── MACD Conditions ──
    macd = latest.get("MACD")
    macd_signal = latest.get("MACD_Signal")
    prev_macd = prev.get("MACD")
    prev_signal = prev.get("MACD_Signal")

    if all(pd.notna(v) for v in [macd, macd_signal, prev_macd, prev_signal]):
        conditions["macd_bullish_cross"] = (prev_macd <= prev_signal and macd > macd_signal)
        conditions["macd_bearish_cross"] = (prev_macd >= prev_signal and macd < macd_signal)
    else:
        conditions["macd_bullish_cross"] = False
        conditions["macd_bearish_cross"] = False

    # ── EMA Alignment ──
    ema9 = latest.get("EMA_9")
    if pd.notna(ema9) and pd.notna(ema20):
        conditions["ema9_above_ema20"] = ema9 > ema20
        conditions["ema9_below_ema20"] = ema9 < ema20
    else:
        conditions["ema9_above_ema20"] = False
        conditions["ema9_below_ema20"] = False

    return conditions


def score_phases(conditions: dict) -> dict:
    """
    Score each of the 6 Gann Cycle phases based on current conditions.

    Returns:
        dict mapping phase number (1-6) to score
    """
    scores = {phase: 0 for phase in range(1, 7)}

    for condition_key, phase_num, weight in PHASE_SCORING_RULES:
        if conditions.get(condition_key, False):
            scores[phase_num] += weight

    return scores


def detect_phase(df: pd.DataFrame) -> dict:
    """
    Detect the current Gann Cycle phase for the given OHLCV DataFrame.

    The DataFrame should already have indicators calculated.

    Returns:
        {
            "phase": int (1-6),
            "phase_name": str,
            "confidence": float (0-100),
            "scores": dict of all phase scores,
            "conditions": dict of evaluated conditions,
            "bias": "BULLISH" | "BEARISH",
            "description": str,
            "color": str,
            "icon": str
        }
    """
    if df is None or len(df) < 30:
        return _default_phase_result()

    # Ensure indicators are calculated
    required_cols = ["EMA_9", "EMA_20", "RSI", "MACD", "ATR", "Volume_Ratio"]
    if not all(col in df.columns for col in required_cols):
        df = calculate_all_indicators(df)

    conditions = evaluate_conditions(df)
    scores = score_phases(conditions)

    # Find winning phase
    winning_phase = max(scores, key=scores.get)
    winning_score = scores[winning_phase]
    max_possible = MAX_PHASE_SCORES.get(winning_phase, 10)

    # Confidence: winning score as percentage of max possible
    confidence = min(100.0, (winning_score / max_possible) * 100) if max_possible > 0 else 0

    # Calculate phase duration (how many bars have been in this phase)
    duration = _calculate_phase_duration(df, winning_phase)

    phase_info = PHASES[winning_phase]

    return {
        "phase": winning_phase,
        "phase_name": phase_info["name"],
        "confidence": round(confidence, 1),
        "duration": duration,
        "scores": scores,
        "conditions": conditions,
        "bias": phase_info["bias"],
        "description": phase_info["description"],
        "color": phase_info["color"],
        "bg_color": phase_info["bg_color"],
        "icon": phase_info["icon"],
    }


def _calculate_phase_duration(df: pd.DataFrame, current_phase: int) -> int:
    """
    Estimate how many recent bars have been in the current phase.
    Looks backwards until the phase changes.
    """
    duration = 1
    # Check up to last 50 bars
    lookback = min(50, len(df) - 30)  # Need 30 bars for indicators

    for i in range(2, lookback + 1):
        sub_df = df.iloc[:-i + 1] if i > 1 else df
        if len(sub_df) < 30:
            break
        conds = evaluate_conditions(sub_df)
        scores = score_phases(conds)
        bar_phase = max(scores, key=scores.get)
        if bar_phase == current_phase:
            duration += 1
        else:
            break

    return duration


def predict_next_phase(current_phase: int, confidence: float) -> dict:
    """
    Predict the next Gann Cycle phase based on cycle order.
    Cycles: 1→2→3→4→5→6→1 (repeating)

    Higher confidence in current phase → more likely to stay.
    Lower confidence → transition more likely.
    """
    next_phase_num = (current_phase % 6) + 1
    next_phase_info = PHASES[next_phase_num]

    # Transition probability: inverse of current confidence
    transition_prob = max(10, 100 - confidence)

    return {
        "next_phase": next_phase_num,
        "next_phase_name": next_phase_info["name"],
        "next_phase_bias": next_phase_info["bias"],
        "transition_probability": round(transition_prob, 1),
    }


def run_single_timeframe(symbol: str, timeframe: str = "1d") -> dict:
    """
    Run Gann Cycle detection for a single symbol and timeframe.

    Returns full phase analysis result.
    """
    tf_config = TIMEFRAMES.get(timeframe, TIMEFRAMES["1d"])
    df = fetch_ohlcv(symbol, period=tf_config["period"],
                     interval=tf_config["interval"])

    if df.empty:
        return _default_phase_result()

    df = calculate_all_indicators(df)
    result = detect_phase(df)
    next_phase = predict_next_phase(result["phase"], result["confidence"])
    result.update(next_phase)
    result["symbol"] = symbol
    result["timeframe"] = timeframe
    result["df"] = df  # Include DataFrame for charting

    return result


def run_multi_timeframe(symbol: str) -> dict:
    """
    Run Gann Cycle detection across all configured timeframes.

    Returns:
        {
            "results": dict mapping tf_key to phase result,
            "confluence": {
                "bullish_count": int,
                "bearish_count": int,
                "total": int,
                "alignment_score": float,
                "dominant_bias": str,
                "strength": str
            }
        }
    """
    tf_data = fetch_multi_timeframe(symbol)
    results = {}

    for tf_key, df in tf_data.items():
        if df.empty or len(df) < 30:
            continue
        df = calculate_all_indicators(df)
        phase_result = detect_phase(df)
        next_phase = predict_next_phase(phase_result["phase"],
                                        phase_result["confidence"])
        phase_result.update(next_phase)
        phase_result["timeframe"] = tf_key
        phase_result["df"] = df
        results[tf_key] = phase_result

    confluence = calculate_tf_confluence(results)

    return {
        "results": results,
        "confluence": confluence,
    }


def calculate_tf_confluence(mtf_results: dict) -> dict:
    """
    Calculate timeframe confluence — how many TFs agree on direction.

    Returns alignment metrics.
    """
    if not mtf_results:
        return {
            "bullish_count": 0,
            "bearish_count": 0,
            "total": 0,
            "alignment_score": 0,
            "dominant_bias": "SIDEWAYS",
            "strength": "WEAK",
        }

    bullish = sum(1 for r in mtf_results.values() if r.get("bias") == "BULLISH")
    bearish = sum(1 for r in mtf_results.values() if r.get("bias") == "BEARISH")
    total = len(mtf_results)

    dominant = "BULLISH" if bullish > bearish else ("BEARISH" if bearish > bullish else "SIDEWAYS")
    alignment = max(bullish, bearish) / total * 100 if total > 0 else 0

    if alignment >= 75:
        strength = "STRONG"
    elif alignment >= 50:
        strength = "MODERATE"
    else:
        strength = "WEAK"

    return {
        "bullish_count": bullish,
        "bearish_count": bearish,
        "total": total,
        "alignment_score": round(alignment, 1),
        "dominant_bias": dominant,
        "strength": strength,
    }


def _default_phase_result() -> dict:
    """Return a default/fallback phase result when data is insufficient."""
    return {
        "phase": 1,
        "phase_name": "Accumulation",
        "confidence": 0.0,
        "duration": 0,
        "scores": {i: 0 for i in range(1, 7)},
        "conditions": {},
        "bias": "SIDEWAYS",
        "description": "Insufficient data for analysis",
        "color": "#888888",
        "bg_color": "rgba(136,136,136,0.10)",
        "icon": "⚪",
    }
