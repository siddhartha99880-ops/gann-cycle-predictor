"""
alerts.py — Alert System
Detects phase transitions, RSI divergences, VIX spikes, and OI divergences.
Persists alerts to SQLite via database.py.
"""
import os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VIX_CAUTION, VIX_HIGH_RISK
from core.database import save_alert


class Alert:
    def __init__(self, symbol, alert_type, severity, message):
        self.symbol = symbol
        self.alert_type = alert_type  # phase_transition, rsi_divergence, vix_spike, oi_divergence
        self.severity = severity      # INFO, WARNING, CRITICAL
        self.message = message
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {"symbol": self.symbol, "alert_type": self.alert_type,
                "severity": self.severity, "message": self.message,
                "timestamp": self.timestamp}


def check_phase_transition(symbol, prev_phase, curr_phase):
    """Fire alert when Gann Cycle phase changes."""
    if prev_phase is None or prev_phase == curr_phase:
        return None
    from config import PHASES
    prev_name = PHASES.get(prev_phase, {}).get("name", f"Phase {prev_phase}")
    curr_name = PHASES.get(curr_phase, {}).get("name", f"Phase {curr_phase}")
    curr_bias = PHASES.get(curr_phase, {}).get("bias", "SIDEWAYS")

    if curr_phase in [2, 5]:  # Key breakout/breakdown phases
        severity = "CRITICAL"
    elif curr_phase in [4, 6]:
        severity = "WARNING"
    else:
        severity = "INFO"

    msg = f"🔄 {symbol}: Phase transition {prev_name} → {curr_name} ({curr_bias})"
    alert = Alert(symbol, "phase_transition", severity, msg)
    save_alert(symbol, alert.alert_type, severity, msg)
    return alert


def check_rsi_divergence(symbol, df):
    """Alert if RSI divergence detected on latest bar."""
    if df is None or len(df) < 2:
        return None
    latest = df.iloc[-1]
    alerts = []

    if latest.get("RSI_Div_Bearish", False):
        msg = f"⚠️ {symbol}: Bearish RSI Divergence — Price making higher high but RSI declining"
        a = Alert(symbol, "rsi_divergence", "WARNING", msg)
        save_alert(symbol, a.alert_type, a.severity, msg)
        alerts.append(a)

    if latest.get("RSI_Div_Bullish", False):
        msg = f"📈 {symbol}: Bullish RSI Divergence — Price making lower low but RSI rising"
        a = Alert(symbol, "rsi_divergence", "INFO", msg)
        save_alert(symbol, a.alert_type, a.severity, msg)
        alerts.append(a)

    return alerts if alerts else None


def check_vix_spike(symbol, vix_value):
    """Alert on elevated VIX levels."""
    if vix_value >= VIX_HIGH_RISK:
        msg = f"🔴 INDIA VIX HIGH ALERT: {vix_value:.1f} — Extreme volatility, high risk environment"
        a = Alert(symbol, "vix_spike", "CRITICAL", msg)
        save_alert(symbol, a.alert_type, a.severity, msg)
        return a
    elif vix_value >= VIX_CAUTION:
        msg = f"⚡ INDIA VIX CAUTION: {vix_value:.1f} — Elevated volatility, widen stop losses"
        a = Alert(symbol, "vix_spike", "WARNING", msg)
        save_alert(symbol, a.alert_type, a.severity, msg)
        return a
    return None


def check_oi_divergence(symbol, price_change, oi_change):
    """Alert on unusual OI pattern."""
    # Short buildup is most dangerous
    if price_change < 0 and oi_change > 0:
        msg = f"📉 {symbol}: Short Buildup detected — Price falling + OI rising. Bearish pressure."
        a = Alert(symbol, "oi_divergence", "WARNING", msg)
        save_alert(symbol, a.alert_type, a.severity, msg)
        return a
    return None


def run_all_checks(symbol, prev_phase, prediction):
    """Run all alert checks and return list of triggered alerts."""
    triggered = []
    curr_phase = prediction.get("gann_cycle_phase", 0)
    df = prediction.get("df")
    vix = prediction.get("india_vix", 14)
    market = prediction.get("market_data", {})
    oi_data = market.get("oi_data", {})
    price_change = 0
    if df is not None and len(df) >= 2:
        price_change = float(df["Close"].iloc[-1] - df["Close"].iloc[-2])

    a = check_phase_transition(symbol, prev_phase, curr_phase)
    if a: triggered.append(a)

    divs = check_rsi_divergence(symbol, df)
    if divs: triggered.extend(divs)

    a = check_vix_spike(symbol, vix)
    if a: triggered.append(a)

    a = check_oi_divergence(symbol, price_change, oi_data.get("oi_change", 0))
    if a: triggered.append(a)

    return triggered
