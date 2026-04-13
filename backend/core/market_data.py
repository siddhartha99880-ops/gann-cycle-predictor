"""
market_data.py — Derivatives & Market Sentiment Data
Fetches PCR, Open Interest, India VIX, and FII/DII activity.
Uses nsepython where available, with graceful fallbacks.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VIX_DEFAULT, PCR_DEFAULT

# Try importing nsepython for NSE derivatives data
try:
    from nsepython import option_chain, nse_quote_ltp
    NSEPYTHON_AVAILABLE = True
except ImportError:
    NSEPYTHON_AVAILABLE = False

import requests
import json
import time


# ──────────────────────────────────────────────
# NSE Headers for direct API calls
# ──────────────────────────────────────────────
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/",
}


def _nse_session():
    """Create a requests session with NSE cookies."""
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    try:
        # Hit main page first to get cookies
        session.get("https://www.nseindia.com", timeout=10)
        time.sleep(0.5)
    except Exception:
        pass
    return session


def get_pcr(symbol: str = "NIFTY") -> dict:
    """
    Fetch Put-Call Ratio from NSE option chain data.

    Returns:
        {
            "pcr": float,        # Put OI / Call OI
            "total_put_oi": int,
            "total_call_oi": int,
            "source": str        # "nsepython" | "nse_api" | "default"
        }
    """
    # Map display names to NSE symbols
    nse_sym_map = {
        "NIFTY 50": "NIFTY",
        "BANK NIFTY": "BANKNIFTY",
        "NIFTY FIN SERVICE": "FINNIFTY",
    }
    nse_sym = nse_sym_map.get(symbol, symbol)

    # Method 1: nsepython
    if NSEPYTHON_AVAILABLE:
        try:
            oc = option_chain(nse_sym)
            if oc and "records" in oc:
                records = oc["records"]
                total_put_oi = sum(
                    r.get("PE", {}).get("openInterest", 0)
                    for r in records.get("data", [])
                )
                total_call_oi = sum(
                    r.get("CE", {}).get("openInterest", 0)
                    for r in records.get("data", [])
                )
                if total_call_oi > 0:
                    return {
                        "pcr": round(total_put_oi / total_call_oi, 3),
                        "total_put_oi": total_put_oi,
                        "total_call_oi": total_call_oi,
                        "source": "nsepython",
                    }
        except Exception:
            pass

    # Method 2: Direct NSE API
    try:
        session = _nse_session()
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={nse_sym}"
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            records = data.get("records", {}).get("data", [])
            total_put_oi = sum(r.get("PE", {}).get("openInterest", 0) for r in records)
            total_call_oi = sum(r.get("CE", {}).get("openInterest", 0) for r in records)
            if total_call_oi > 0:
                return {
                    "pcr": round(total_put_oi / total_call_oi, 3),
                    "total_put_oi": total_put_oi,
                    "total_call_oi": total_call_oi,
                    "source": "nse_api",
                }
    except Exception:
        pass

    # Fallback: default value
    return {
        "pcr": PCR_DEFAULT,
        "total_put_oi": 0,
        "total_call_oi": 0,
        "source": "default",
    }


def get_oi_data(symbol: str = "NIFTY", price_change: float = 0) -> dict:
    """
    Fetch Open Interest data and determine OI signal.

    OI Signal interpretation:
    - Price↑ + OI↑ = Long Buildup (Bullish)
    - Price↑ + OI↓ = Short Covering (Mildly Bullish)
    - Price↓ + OI↑ = Short Buildup (Bearish)
    - Price↓ + OI↓ = Long Unwinding (Mildly Bearish)

    Returns:
        {
            "oi_change": float,
            "oi_change_pct": float,
            "oi_signal": str,
            "interpretation": str,
            "source": str
        }
    """
    nse_sym_map = {
        "NIFTY 50": "NIFTY",
        "BANK NIFTY": "BANKNIFTY",
        "NIFTY FIN SERVICE": "FINNIFTY",
    }
    nse_sym = nse_sym_map.get(symbol, symbol)

    oi_change = 0
    source = "estimated"

    # Try nsepython
    if NSEPYTHON_AVAILABLE:
        try:
            oc = option_chain(nse_sym)
            if oc and "records" in oc:
                records = oc["records"].get("data", [])
                total_oi = sum(
                    r.get("CE", {}).get("openInterest", 0) +
                    r.get("PE", {}).get("openInterest", 0)
                    for r in records
                )
                total_oi_change = sum(
                    r.get("CE", {}).get("changeinOpenInterest", 0) +
                    r.get("PE", {}).get("changeinOpenInterest", 0)
                    for r in records
                )
                oi_change = total_oi_change
                source = "nsepython"
        except Exception:
            pass

    # Determine OI signal
    oi_up = oi_change > 0
    price_up = price_change > 0

    if price_up and oi_up:
        signal = "Long Buildup"
        interpretation = "Bullish — Fresh buying with rising open interest"
    elif price_up and not oi_up:
        signal = "Short Covering"
        interpretation = "Mildly Bullish — Shorts closing positions"
    elif not price_up and oi_up:
        signal = "Short Buildup"
        interpretation = "Bearish — Fresh selling with rising open interest"
    else:
        signal = "Long Unwinding"
        interpretation = "Mildly Bearish — Longs closing positions"

    return {
        "oi_change": oi_change,
        "oi_change_pct": 0,
        "oi_signal": signal,
        "interpretation": interpretation,
        "source": source,
    }


def get_india_vix() -> dict:
    """
    Fetch India VIX (volatility index / fear gauge).

    Returns:
        {
            "vix": float,
            "vix_level": "LOW" | "MEDIUM" | "HIGH",
            "interpretation": str,
            "source": str
        }
    """
    vix_value = VIX_DEFAULT
    source = "default"

    # Method 1: yfinance
    try:
        import yfinance as yf
        vix_ticker = yf.Ticker("^INDIAVIX")
        hist = vix_ticker.history(period="5d")
        if not hist.empty:
            vix_value = float(hist["Close"].iloc[-1])
            source = "yfinance"
    except Exception:
        pass

    # Method 2: NSE API fallback
    if source == "default":
        try:
            session = _nse_session()
            resp = session.get("https://www.nseindia.com/api/allIndices", timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for idx in data.get("data", []):
                    if "VIX" in idx.get("index", "").upper():
                        vix_value = float(idx.get("last", VIX_DEFAULT))
                        source = "nse_api"
                        break
        except Exception:
            pass

    # Classify VIX level
    if vix_value < 15:
        level = "LOW"
        interp = "Low volatility — Complacency, favor directional strategies"
    elif vix_value < 20:
        level = "MEDIUM"
        interp = "Normal volatility — Standard market conditions"
    elif vix_value < 25:
        level = "HIGH"
        interp = "Elevated volatility — Caution advised, wider stop losses"
    else:
        level = "HIGH"
        interp = "Extreme volatility — High risk, consider hedging"

    return {
        "vix": round(vix_value, 2),
        "vix_level": level,
        "interpretation": interp,
        "source": source,
    }


def get_fii_dii_activity() -> dict:
    """
    Fetch FII/DII net buying/selling activity.
    Falls back to manual display if scraping fails.

    Returns:
        {
            "fii_net": float,  # Positive = net buyer, negative = net seller
            "dii_net": float,
            "fii_activity": "Net Buyer" | "Net Seller",
            "dii_activity": "Net Buyer" | "Net Seller",
            "source": str
        }
    """
    # Try NSE API
    try:
        session = _nse_session()
        resp = session.get(
            "https://www.nseindia.com/api/fiidiiTradeReact",
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            fii_net = 0
            dii_net = 0
            for item in data:
                cat = item.get("category", "")
                buy = float(item.get("buyValue", 0))
                sell = float(item.get("sellValue", 0))
                if "FII" in cat.upper() or "FPI" in cat.upper():
                    fii_net = buy - sell
                elif "DII" in cat.upper():
                    dii_net = buy - sell

            return {
                "fii_net": round(fii_net, 2),
                "dii_net": round(dii_net, 2),
                "fii_activity": "Net Buyer" if fii_net > 0 else "Net Seller",
                "dii_activity": "Net Buyer" if dii_net > 0 else "Net Seller",
                "source": "nse_api",
            }
    except Exception:
        pass

    # Fallback: neutral
    return {
        "fii_net": 0,
        "dii_net": 0,
        "fii_activity": "Data Unavailable",
        "dii_activity": "Data Unavailable",
        "source": "default",
    }


def get_all_market_data(symbol: str = "NIFTY 50",
                        price_change: float = 0) -> dict:
    """
    Fetch all market sentiment data in one call.

    Returns combined dict of PCR, OI, VIX, and FII/DII data.
    """
    pcr_data = get_pcr(symbol)
    oi_data = get_oi_data(symbol, price_change)
    vix_data = get_india_vix()
    fii_dii = get_fii_dii_activity()

    return {
        "pcr": pcr_data["pcr"],
        "pcr_data": pcr_data,
        "oi_data": oi_data,
        "oi_signal": oi_data["oi_signal"],
        "india_vix": vix_data["vix"],
        "vix_data": vix_data,
        "fii_activity": fii_dii["fii_activity"],
        "dii_activity": fii_dii["dii_activity"],
        "fii_dii_data": fii_dii,
    }
