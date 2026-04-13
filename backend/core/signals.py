"""
signals.py — Entry/Exit Signal Generator
Generates actionable trading signals with entry zones, targets,
stop losses, and instrument suggestions based on Gann Cycle phase.
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PHASES


def generate_entry_exit(prediction: dict) -> dict:
    """
    Generate detailed entry/exit signals from a prediction.

    This wraps around the predictor's built-in levels and adds
    instrument suggestions and formatted output.

    Args:
        prediction: Full prediction dict from predictor.generate_prediction()

    Returns:
        {
            "entry_zone": [low, high],
            "targets": [t1, t2, t3],
            "stop_loss": float,
            "risk_reward": str,
            "instrument": str,
            "action": str,
            "position_type": str,
        }
    """
    bias = prediction.get("directional_bias", "SIDEWAYS")
    strength = prediction.get("signal_strength", "WEAK")
    vix = prediction.get("india_vix", 14)
    phase = prediction.get("gann_cycle_phase", 1)
    entry_zone = prediction.get("entry_zone", [])
    targets = prediction.get("targets", [])
    stop_loss = prediction.get("stop_loss", 0)
    risk_reward = prediction.get("risk_reward", "N/A")

    # Determine action
    if bias == "BULLISH":
        action = "BUY"
        position_type = "LONG"
    elif bias == "BEARISH":
        action = "SELL"
        position_type = "SHORT"
    else:
        action = "WAIT"
        position_type = "NEUTRAL"

    # Instrument suggestion based on signal strength and VIX
    instrument = _suggest_instrument(bias, strength, vix, phase)

    return {
        "action": action,
        "position_type": position_type,
        "entry_zone": entry_zone,
        "targets": targets,
        "stop_loss": stop_loss,
        "risk_reward": risk_reward,
        "instrument": instrument,
        "signal_strength": strength,
        "bias": bias,
    }


def _suggest_instrument(bias: str, strength: str, vix: float,
                        phase: int) -> str:
    """
    Suggest the best instrument based on conditions.

    - STRONG signal + low VIX → Futures (higher leverage)
    - MODERATE signal → Options (limited risk)
    - WEAK signal → Spot / avoid
    - High VIX → Options selling strategies
    """
    if strength == "STRONG":
        if vix < 18:
            return "Futures"
        else:
            return "Options (ATM CE)" if bias == "BULLISH" else "Options (ATM PE)"
    elif strength == "MODERATE":
        if bias == "BULLISH":
            return "Options (Slightly OTM CE)"
        elif bias == "BEARISH":
            return "Options (Slightly OTM PE)"
        else:
            return "Spot / Cash"
    else:
        return "Cash — Wait for clearer signal"


def format_signal_card(prediction: dict) -> dict:
    """
    Format prediction into a display-friendly signal card dict.
    Used by the UI to render the signal card component.
    """
    signal = generate_entry_exit(prediction)
    phase_info = PHASES.get(prediction.get("gann_cycle_phase", 1), PHASES[1])

    # Format entry zone
    ez = signal["entry_zone"]
    entry_str = f"₹{ez[0]:,.2f} — ₹{ez[1]:,.2f}" if len(ez) == 2 else "N/A"

    # Format targets
    tgts = signal["targets"]
    target_strs = [f"₹{t:,.2f}" for t in tgts] if tgts else ["N/A"]

    return {
        "action": signal["action"],
        "action_color": "#00d4aa" if signal["action"] == "BUY" else (
            "#e74c3c" if signal["action"] == "SELL" else "#f39c12"
        ),
        "position_type": signal["position_type"],
        "bias": signal["bias"],
        "signal_strength": signal["signal_strength"],
        "entry_zone_str": entry_str,
        "targets_str": target_strs,
        "stop_loss_str": f"₹{signal['stop_loss']:,.2f}" if signal["stop_loss"] else "N/A",
        "risk_reward": signal["risk_reward"],
        "instrument": signal["instrument"],
        "phase_name": prediction.get("phase_name", "Unknown"),
        "phase_icon": phase_info["icon"],
        "phase_color": phase_info["color"],
        "confidence": prediction.get("composite_confidence",
                                     prediction.get("phase_confidence", 0)),
    }
