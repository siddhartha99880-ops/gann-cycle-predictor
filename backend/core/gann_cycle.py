"""
gann_cycle.py — ★ CORE ENGINE ★
Gann Cycle Phase Detector — the heart of the prediction system.

Implements W.D. Gann's true cyclical market model adapted into 6 phases:
Uses genuine Gann Math (Square of 9 support/resistance) and Gann Angles
(1x1, 1x2, 2x1) to mathematically pinpoint institutional turning points.
"""

import os
import sys
import math
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PHASES, PHASE_SCORING_RULES, MAX_PHASE_SCORES, TIMEFRAMES
from core.indicators import calculate_all_indicators
from core.data_fetcher import fetch_ohlcv, fetch_multi_timeframe

def get_sq9_levels(price: float) -> list:
    """Calculate Square of 9 support & resistance levels dynamically."""
    if price <= 0:
        return []
    
    root = math.sqrt(price)
    
    return {
        "sup_360": (root - 2.0)**2,
        "sup_180": (root - 1.0)**2,
        "sup_90":  (root - 0.5)**2,
        "sup_45":  (root - 0.25)**2,
        "res_45":  (root + 0.25)**2,
        "res_90":  (root + 0.5)**2,
        "res_180": (root + 1.0)**2,
        "res_360": (root + 2.0)**2,
    }


def evaluate_conditions(df: pd.DataFrame) -> dict:
    """
    Evaluate TRUE GANN mathematical conditions for the latest bar.
    """
    if len(df) < 60:
        return {}

    # Find the major pivot in the last 60 bars
    lookback = df.tail(60)
    high_px = lookback["High"].max()
    low_px = lookback["Low"].min()
    
    idx_high = lookback["High"].idxmax()
    idx_low = lookback["Low"].idxmax()
    
    # Are we closer to the high or the low in time? 
    # If the low was more recent, it's an uptrend cycle.
    bars_since_high = len(df) - df.index.get_loc(idx_high) - 1
    bars_since_low = len(df) - df.index.get_loc(idx_low) - 1
    
    is_uptrend = bars_since_low < bars_since_high
    
    pivot = low_px if is_uptrend else high_px
    bars_since = bars_since_low if is_uptrend else bars_since_high
    
    latest = df.iloc[-1]
    close = latest["Close"]
    
    # Gann Angles based on ATR scaling
    atr_avg = lookback["ATR"].mean() if "ATR" in lookback.columns else (high_px - low_px) * 0.05
    if pd.isna(atr_avg) or atr_avg == 0:
        atr_avg = close * 0.01

    if is_uptrend:
        angle_1x1 = pivot + (bars_since * atr_avg)
        angle_1x2 = pivot + (bars_since * atr_avg * 0.5)
        angle_2x1 = pivot + (bars_since * atr_avg * 2.0)
    else:
        angle_1x1 = pivot - (bars_since * atr_avg)
        angle_1x2 = pivot - (bars_since * atr_avg * 0.5)
        angle_2x1 = pivot - (bars_since * atr_avg * 2.0)
        
    sq9 = get_sq9_levels(close)
    
    conditions = {}
    
    # Square of 9 Conditions
    distance_to_nearest = 999999.0
    nearest_level_type = None
    
    for k, v in sq9.items():
        dist = abs(close - v) / close
        if dist < distance_to_nearest:
            distance_to_nearest = dist
            nearest_level_type = "res" if "res" in k else "sup"
            
    is_near = distance_to_nearest < 0.015 # within 1.5% of a major Gann number
    
    conditions["near_gann_support"] = (is_near and nearest_level_type == "sup")
    conditions["near_gann_resistance"] = (is_near and nearest_level_type == "res")
    
    # Gann Angle Conditions
    if is_uptrend:
        conditions["above_gann_1x1"] = close > angle_1x1
        conditions["below_gann_1x1"] = close < angle_1x1
        conditions["above_gann_1x2"] = close > angle_1x2
        conditions["below_gann_1x2_bear"] = False
    else:
        conditions["above_gann_1x1"] = False
        conditions["below_gann_1x1"] = close < angle_1x1
        conditions["above_gann_1x2"] = False
        conditions["below_gann_1x2_bear"] = close < angle_1x2
        
    # Time Cycles
    # True Gann uses quarters and thirds of the 360-day year (90, 120, 180 chars)
    # We'll use bar offsets for simplicity in intraday
    conditions["bullish_time_cycle"] = is_uptrend and bars_since in [45, 90, 120, 180]
    conditions["bearish_time_cycle"] = not is_uptrend and bars_since in [45, 90, 120, 180]
    conditions["bearish_time_cycle_active"] = not is_uptrend

    # Support / Resistance breaks
    prev_close = df.iloc[-2]["Close"] if len(df) > 1 else close
    conditions["breaking_sq9_res"] = prev_close < sq9["res_45"] and close > sq9["res_45"]
    conditions["cleared_sq9_res"] = close > sq9["res_90"]
    conditions["breaking_sq9_sup"] = prev_close > sq9["sup_45"] and close < sq9["sup_45"]
    conditions["cleared_sq9_sup"] = close < sq9["sup_90"]

    # Momentum confirmation
    vol_ratio = latest.get("Volume_Ratio", 1.0)
    rsi = latest.get("RSI", 50)
    macd = latest.get("MACD", 0)
    
    conditions["price_sideways"] = vol_ratio < 0.8 and 40 <= rsi <= 60
    conditions["strong_momentum"] = vol_ratio > 1.2 and rsi > 60 and macd > 0
    conditions["losing_momentum"] = rsi_divergence(df)
    conditions["extreme_down_momentum"] = vol_ratio > 1.5 and rsi < 30 and macd < 0

    return conditions


def rsi_divergence(df: pd.DataFrame) -> bool:
    """Basic RSI divergence check vs Price"""
    if len(df) < 10 or "RSI" not in df.columns: return False
    p1 = df["Close"].iloc[-10]
    p2 = df["Close"].iloc[-1]
    r1 = df["RSI"].iloc[-10]
    r2 = df["RSI"].iloc[-1]
    
    # Bearish div: Price higher, RSI lower
    if p2 > p1 and r2 < r1: return True
    return False


def score_phases(conditions: dict) -> dict:
    scores = {phase: 0 for phase in range(1, 7)}
    for condition_key, phase_num, weight in PHASE_SCORING_RULES:
        if conditions.get(condition_key, False):
            scores[phase_num] += weight
    return scores


def detect_phase(df: pd.DataFrame) -> dict:
    if df is None or len(df) < 60:
        return _default_phase_result()

    required_cols = ["RSI", "MACD", "ATR", "Volume_Ratio"]
    if not all(col in df.columns for col in required_cols):
        df = calculate_all_indicators(df)

    conditions = evaluate_conditions(df)
    scores = score_phases(conditions)

    # Find winning phase
    winning_phase = max(scores, key=scores.get)
    winning_score = scores[winning_phase]
    max_possible = MAX_PHASE_SCORES.get(winning_phase, 10)

    # Prevent 0/0 and calc confidence
    confidence = min(100.0, (winning_score / max_possible) * 100) if max_possible > 0 else 0.0

    duration = 1

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

def predict_next_phase(current_phase: int, confidence: float) -> dict:
    next_phase_num = (current_phase % 6) + 1
    next_phase_info = PHASES[next_phase_num]
    transition_prob = max(10, 100 - confidence)

    return {
        "next_phase": next_phase_num,
        "next_phase_name": next_phase_info["name"],
        "next_phase_bias": next_phase_info["bias"],
        "transition_probability": round(transition_prob, 1),
    }

def run_single_timeframe(symbol: str, timeframe: str = "1d") -> dict:
    tf_config = TIMEFRAMES.get(timeframe, TIMEFRAMES["1d"])
    df = fetch_ohlcv(symbol, period=tf_config["period"], interval=tf_config["interval"])

    if df.empty:
        return _default_phase_result()

    df = calculate_all_indicators(df)
    result = detect_phase(df)
    next_phase = predict_next_phase(result["phase"], result["confidence"])
    result.update(next_phase)
    result["symbol"] = symbol
    result["timeframe"] = timeframe
    result["df"] = df

    return result

def run_multi_timeframe(symbol: str) -> dict:
    tf_data = fetch_multi_timeframe(symbol)
    results = {}

    for tf_key, df in tf_data.items():
        if df.empty or len(df) < 60:
            continue
        df = calculate_all_indicators(df)
        phase_result = detect_phase(df)
        next_phase = predict_next_phase(phase_result["phase"], phase_result["confidence"])
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
    if not mtf_results:
        return {"bullish_count": 0, "bearish_count": 0, "total": 0, "alignment_score": 0, "dominant_bias": "SIDEWAYS", "strength": "WEAK"}
    bullish = sum(1 for r in mtf_results.values() if r.get("bias") == "BULLISH")
    bearish = sum(1 for r in mtf_results.values() if r.get("bias") == "BEARISH")
    total = len(mtf_results)
    dominant = "BULLISH" if bullish > bearish else ("BEARISH" if bearish > bullish else "SIDEWAYS")
    alignment = max(bullish, bearish) / total * 100 if total > 0 else 0
    strength = "STRONG" if alignment >= 75 else "MODERATE" if alignment >= 50 else "WEAK"

    return {
        "bullish_count": bullish, "bearish_count": bearish, "total": total,
        "alignment_score": round(alignment, 1), "dominant_bias": dominant, "strength": strength
    }

def _default_phase_result() -> dict:
    return {
        "phase": 1, "phase_name": "Accumulation", "confidence": 0.0, "duration": 0,
        "scores": {i: 0 for i in range(1, 7)}, "conditions": {}, "bias": "SIDEWAYS",
        "description": "Insufficient data for Gann Math", "color": "#888888",
        "bg_color": "rgba(136,136,136,0.10)", "icon": "⚪",
    }
