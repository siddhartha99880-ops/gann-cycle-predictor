"""
predictor.py — Futures Movement Predictor
Combines Gann Cycle phase detection with market sentiment data
to generate comprehensive trading predictions.
"""

import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PHASES, SIGNAL_STRENGTH_THRESHOLDS
from core.gann_cycle import run_single_timeframe, run_multi_timeframe, detect_phase, predict_next_phase
from core.market_data import get_all_market_data
from core.indicators import calculate_all_indicators
from core.data_fetcher import fetch_ohlcv


def generate_prediction(symbol: str, timeframe: str = "1d") -> dict:
    """
    Generate a comprehensive futures movement prediction.

    This is the main prediction function that combines:
    1. Gann Cycle phase detection
    2. Market sentiment (PCR, OI, VIX, FII/DII)
    3. Multi-timeframe confluence
    4. Entry/exit levels

    Returns the full prediction dict matching the output format spec.
    """
    # ── 1. Run Gann Cycle detection ──
    cycle_result = run_single_timeframe(symbol, timeframe)
    df = cycle_result.get("df", pd.DataFrame())

    if df.empty:
        return _empty_prediction(symbol, timeframe)

    # ── 2. Get multi-TF confluence ──
    mtf = run_multi_timeframe(symbol)
    confluence = mtf.get("confluence", {})

    # ── 3. Fetch market sentiment data ──
    price_change = 0
    if len(df) >= 2:
        price_change = float(df["Close"].iloc[-1] - df["Close"].iloc[-2])

    market = get_all_market_data(symbol, price_change)

    # ── 4. Calculate composite confidence ──
    base_confidence = cycle_result.get("confidence", 50)
    confluence_boost = _confluence_boost(confluence)
    sentiment_boost = _sentiment_boost(market, cycle_result.get("bias", "SIDEWAYS"))
    composite_confidence = min(100, base_confidence + confluence_boost + sentiment_boost)

    # ── 5. Determine signal strength ──
    signal_strength = _get_signal_strength(composite_confidence, confluence)

    # ── 6. Calculate target range and key levels ──
    levels = _calculate_levels(df, cycle_result.get("bias", "SIDEWAYS"))

    # ── 7. Generate entry/exit ──
    entry_exit = _generate_entry_exit(df, cycle_result.get("bias", "SIDEWAYS"), levels)

    # ── 8. Get options suggestion ──
    from core.options_strategy import suggest_strategy
    options_sug = suggest_strategy(
        bias=cycle_result.get("bias", "SIDEWAYS"),
        vix=market.get("india_vix", 14),
        current_price=float(df["Close"].iloc[-1]),
    )

    # ── 9. Build alert text ──
    alert_text = _build_alert_text(cycle_result, confluence, market)

    # ── 10. Determine directional bias (may override to SIDEWAYS) ──
    bias = cycle_result.get("bias", "SIDEWAYS")
    if confluence.get("alignment_score", 0) < 40 and composite_confidence < 40:
        bias = "SIDEWAYS"

    # ── Assemble full prediction ──
    prediction = {
        "symbol": symbol,
        "timeframe": timeframe,
        "gann_cycle_phase": cycle_result.get("phase", 0),
        "phase_name": cycle_result.get("phase_name", "Unknown"),
        "phase_confidence": round(base_confidence, 1),
        "phase_duration_bars": cycle_result.get("duration", 0),
        "next_phase_predicted": cycle_result.get("next_phase_name", "Unknown"),
        "directional_bias": bias,
        "signal_strength": signal_strength,
        "composite_confidence": round(composite_confidence, 1),
        "entry_zone": entry_exit.get("entry_zone", []),
        "targets": entry_exit.get("targets", []),
        "stop_loss": entry_exit.get("stop_loss", 0),
        "risk_reward": entry_exit.get("risk_reward", "N/A"),
        "pcr": market.get("pcr", 0),
        "india_vix": market.get("india_vix", 0),
        "oi_signal": market.get("oi_signal", "N/A"),
        "fii_activity": market.get("fii_activity", "N/A"),
        "dii_activity": market.get("dii_activity", "N/A"),
        "options_suggestion": options_sug.get("suggestion", "N/A"),
        "alert": alert_text,
        "support": levels.get("support", 0),
        "resistance": levels.get("resistance", 0),
        "upper_band": levels.get("upper_band", 0),
        "lower_band": levels.get("lower_band", 0),
        "confluence": confluence,
        "market_data": market,
        "cycle_result": cycle_result,
        "df": df,
    }

    return prediction


def _confluence_boost(confluence: dict) -> float:
    """Add confidence boost based on TF confluence."""
    alignment = confluence.get("alignment_score", 0)
    if alignment >= 80:
        return 15
    elif alignment >= 60:
        return 8
    elif alignment >= 40:
        return 3
    return -5


def _sentiment_boost(market: dict, bias: str) -> float:
    """Add confidence boost based on market sentiment alignment."""
    boost = 0
    pcr = market.get("pcr", 1.0)
    oi_signal = market.get("oi_signal", "")
    fii = market.get("fii_activity", "")

    if bias == "BULLISH":
        if pcr > 0.7:
            boost += 3  # More puts = bullish sentiment
        if oi_signal == "Long Buildup":
            boost += 5
        if fii == "Net Buyer":
            boost += 3
    elif bias == "BEARISH":
        if pcr < 0.7:
            boost += 3
        if oi_signal in ["Short Buildup"]:
            boost += 5
        if fii == "Net Seller":
            boost += 3

    return boost


def _get_signal_strength(confidence: float, confluence: dict) -> str:
    """Determine signal strength based on confidence and confluence."""
    alignment = confluence.get("alignment_score", 0)
    if confidence >= 75 and alignment >= 60:
        return "STRONG"
    elif confidence >= 50:
        return "MODERATE"
    return "WEAK"


def _calculate_levels(df: pd.DataFrame, bias: str) -> dict:
    """
    Calculate support, resistance, and target bands.
    Uses recent swing highs/lows and ATR for bands.
    """
    close = float(df["Close"].iloc[-1])
    atr = float(df["ATR"].iloc[-1]) if "ATR" in df.columns and pd.notna(df["ATR"].iloc[-1]) else close * 0.015

    # Swing high/low over last 20 bars
    lookback = min(20, len(df))
    recent = df.tail(lookback)
    swing_high = float(recent["High"].max())
    swing_low = float(recent["Low"].min())

    # Support/Resistance
    support = swing_low
    resistance = swing_high

    # ATR-based target bands for next session
    upper_band = round(close + 1.5 * atr, 2)
    lower_band = round(close - 1.5 * atr, 2)

    return {
        "support": round(support, 2),
        "resistance": round(resistance, 2),
        "upper_band": upper_band,
        "lower_band": lower_band,
        "atr": round(atr, 2),
    }


def _generate_entry_exit(df: pd.DataFrame, bias: str, levels: dict) -> dict:
    """
    Generate entry zone, targets, stop loss, and risk:reward.
    """
    close = float(df["Close"].iloc[-1])
    atr = levels.get("atr", close * 0.015)

    if bias == "BULLISH":
        entry_low = round(close - 0.25 * atr, 2)
        entry_high = round(close + 0.25 * atr, 2)
        t1 = round(close + 1.0 * atr, 2)
        t2 = round(close + 2.0 * atr, 2)
        t3 = round(close + 3.0 * atr, 2)
        sl = round(levels["support"] - 0.25 * atr, 2)
    elif bias == "BEARISH":
        entry_low = round(close - 0.25 * atr, 2)
        entry_high = round(close + 0.25 * atr, 2)
        t1 = round(close - 1.0 * atr, 2)
        t2 = round(close - 2.0 * atr, 2)
        t3 = round(close - 3.0 * atr, 2)
        sl = round(levels["resistance"] + 0.25 * atr, 2)
    else:
        entry_low = round(close - 0.25 * atr, 2)
        entry_high = round(close + 0.25 * atr, 2)
        t1 = round(close + 0.5 * atr, 2)
        t2 = round(close + 1.0 * atr, 2)
        t3 = round(close + 1.5 * atr, 2)
        sl = round(close - 1.0 * atr, 2)

    # Risk:Reward calculation
    entry_mid = (entry_low + entry_high) / 2
    risk = abs(entry_mid - sl)
    reward = abs(t2 - entry_mid)
    rr = f"1:{round(reward / risk, 1)}" if risk > 0 else "N/A"

    return {
        "entry_zone": [entry_low, entry_high],
        "targets": [t1, t2, t3],
        "stop_loss": sl,
        "risk_reward": rr,
    }


def _build_alert_text(cycle_result: dict, confluence: dict, market: dict) -> str:
    """Build a summary alert text string."""
    parts = []

    phase_name = cycle_result.get("phase_name", "")
    confidence = cycle_result.get("confidence", 0)
    parts.append(f"Phase: {phase_name} ({confidence:.0f}% confidence)")

    # Confluence
    bull = confluence.get("bullish_count", 0)
    total = confluence.get("total", 0)
    if total > 0:
        parts.append(f"TF Confluence: {bull}/{total} bullish")

    # VIX alert
    vix = market.get("india_vix", 14)
    if vix > 25:
        parts.append(f"⚠️ VIX HIGH: {vix}")
    elif vix > 20:
        parts.append(f"⚡ VIX Elevated: {vix}")

    # OI signal
    oi = market.get("oi_signal", "")
    if oi:
        parts.append(f"OI: {oi}")

    return " | ".join(parts)


def _empty_prediction(symbol: str, timeframe: str) -> dict:
    """Return empty prediction when data is unavailable."""
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "gann_cycle_phase": 0,
        "phase_name": "No Data",
        "phase_confidence": 0,
        "phase_duration_bars": 0,
        "next_phase_predicted": "N/A",
        "directional_bias": "SIDEWAYS",
        "signal_strength": "WEAK",
        "composite_confidence": 0,
        "entry_zone": [],
        "targets": [],
        "stop_loss": 0,
        "risk_reward": "N/A",
        "pcr": 0,
        "india_vix": 0,
        "oi_signal": "N/A",
        "fii_activity": "N/A",
        "dii_activity": "N/A",
        "options_suggestion": "N/A",
        "alert": "No data available",
        "support": 0,
        "resistance": 0,
        "upper_band": 0,
        "lower_band": 0,
        "confluence": {},
        "market_data": {},
        "cycle_result": {},
        "df": pd.DataFrame(),
    }
