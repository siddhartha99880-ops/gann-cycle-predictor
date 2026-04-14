"""
options_strategy.py — Options Strategy Suggester
Recommends options strategies based on Gann Cycle phase, VIX level,
and market conditions.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPTIONS_STRATEGIES

def _classify_vix(vix):
    if vix < 15: return "LOW"
    elif vix < 22: return "MEDIUM"
    return "HIGH"

def _get_atm_strike(price, step=50):
    return round(price / step) * step

def suggest_strategy(bias, vix, current_price, days_to_expiry=7, step=50):
    vix_level = _classify_vix(vix)
    atm = _get_atm_strike(current_price, step)
    strategy_key = (bias, vix_level)
    name = OPTIONS_STRATEGIES.get(strategy_key, "Iron Condor")
    legs, suggestion, rationale = [], "", ""
    max_risk, max_reward = "Defined", "Defined"

    if name == "Bull Call Spread":
        bs, ss = atm, atm + 2*step
        legs = [{"type":"BUY","option":"CE","strike":bs},{"type":"SELL","option":"CE","strike":ss}]
        suggestion = f"Bull Call Spread {bs}-{ss} CE"
        rationale = f"Bullish + low VIX ({vix:.1f}). Limited risk."
    elif name == "Long Call":
        legs = [{"type":"BUY","option":"CE","strike":atm}]
        suggestion = f"Long Call {atm} CE"
        rationale = f"Bullish + moderate VIX ({vix:.1f})."
        max_risk, max_reward = "Premium paid", "Unlimited"
    elif "Bull Put" in name:
        ss, bs = atm, atm - 2*step
        legs = [{"type":"SELL","option":"PE","strike":ss},{"type":"BUY","option":"PE","strike":bs}]
        suggestion = f"Bull Put Spread {bs}-{ss} PE"
        rationale = f"Bullish + high VIX ({vix:.1f}). Sell premium."
    elif name == "Bear Put Spread":
        bs, ss = atm, atm - 2*step
        legs = [{"type":"BUY","option":"PE","strike":bs},{"type":"SELL","option":"PE","strike":ss}]
        suggestion = f"Bear Put Spread {ss}-{bs} PE"
        rationale = f"Bearish + low VIX ({vix:.1f})."
    elif name == "Long Put":
        legs = [{"type":"BUY","option":"PE","strike":atm}]
        suggestion = f"Long Put {atm} PE"
        rationale = f"Bearish + moderate VIX ({vix:.1f})."
        max_risk, max_reward = "Premium paid", "Substantial"
    elif "Bear Call" in name:
        ss, bs = atm, atm + 2*step
        legs = [{"type":"SELL","option":"CE","strike":ss},{"type":"BUY","option":"CE","strike":bs}]
        suggestion = f"Bear Call Spread {ss}-{bs} CE"
        rationale = f"Bearish + high VIX ({vix:.1f}). Sell premium."
    elif name == "Long Straddle":
        legs = [{"type":"BUY","option":"CE","strike":atm},{"type":"BUY","option":"PE","strike":atm}]
        suggestion = f"Long Straddle {atm}"
        rationale = f"Breakout expected, low VIX ({vix:.1f})."
        max_risk, max_reward = "Premiums paid", "Unlimited"
    elif name == "Iron Condor":
        legs = [
            {"type":"SELL","option":"CE","strike":atm+2*step},{"type":"BUY","option":"CE","strike":atm+4*step},
            {"type":"SELL","option":"PE","strike":atm-2*step},{"type":"BUY","option":"PE","strike":atm-4*step},
        ]
        suggestion = f"Iron Condor {atm-2*step}/{atm+2*step}"
        rationale = f"Range-bound, medium VIX ({vix:.1f})."
    elif name == "Short Straddle":
        legs = [{"type":"SELL","option":"CE","strike":atm},{"type":"SELL","option":"PE","strike":atm}]
        suggestion = f"Short Straddle {atm}"
        rationale = f"Sideways + high VIX ({vix:.1f}). Sell premium."
        max_risk, max_reward = "Unlimited", "Premiums received"

    exp_range = [
        round(current_price - current_price*(vix/100)*(days_to_expiry/365)**0.5, 2),
        round(current_price + current_price*(vix/100)*(days_to_expiry/365)**0.5, 2),
    ]
    return {"strategy":name,"suggestion":suggestion,"legs":legs,"rationale":rationale,
            "expected_range":exp_range,"max_risk":max_risk,"max_reward":max_reward,
            "vix":vix,"vix_level":vix_level,"atm_strike":atm,"days_to_expiry":days_to_expiry}
