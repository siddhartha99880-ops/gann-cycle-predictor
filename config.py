"""
config.py — Central configuration for Gann Cycle Predictor
Contains all constants, symbol maps, phase definitions, and scoring weights.
"""

# ──────────────────────────────────────────────
# SYMBOL REGISTRY
# Maps display names to Yahoo Finance ticker symbols
# ──────────────────────────────────────────────
SYMBOL_MAP = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "NIFTY FIN SERVICE": "NIFTY_FIN_SERVICE.NS",
    "NIFTY MIDCAP 50": "^NSEMDCP50",
    "SENSEX": "^BSESN",
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "INFY": "INFY.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "ITC": "ITC.NS",
    "SBIN": "SBIN.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "LT": "LT.NS",
    "AXISBANK": "AXISBANK.NS",
    "ASIANPAINT": "ASIANPAINT.NS",
    "MARUTI": "MARUTI.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "SUNPHARMA": "SUNPHARMA.NS",
    "TITAN": "TITAN.NS",
    "WIPRO": "WIPRO.NS",
    "ADANIENT": "ADANIENT.NS",
}

# Symbols for which we fetch derivatives data (PCR, OI)
DERIVATIVES_SYMBOLS = ["NIFTY 50", "BANK NIFTY", "NIFTY FIN SERVICE"]

# Index symbols for sector heatmap
INDEX_SYMBOLS = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
    "NIFTY MIDCAP 50": "^NSEMDCP50",
}

# ──────────────────────────────────────────────
# TIMEFRAME DEFINITIONS
# ──────────────────────────────────────────────
TIMEFRAMES = {
    "5m": {"interval": "5m", "period": "5d", "label": "5 Min"},
    "15m": {"interval": "15m", "period": "60d", "label": "15 Min"},
    "1h": {"interval": "1h", "period": "60d", "label": "1 Hour"},
    "1d": {"interval": "1d", "period": "1y", "label": "Daily"},
    "1wk": {"interval": "1wk", "period": "2y", "label": "Weekly"},
}

DEFAULT_TIMEFRAME = "1d"

# ──────────────────────────────────────────────
# TECHNICAL INDICATOR PARAMETERS
# ──────────────────────────────────────────────
EMA_LENGTHS = [9, 20, 50, 200]
RSI_LENGTH = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ATR_LENGTH = 14
VOLUME_AVG_PERIOD = 20

# ──────────────────────────────────────────────
# GYAN CYCLE PHASE DEFINITIONS
# ──────────────────────────────────────────────
PHASES = {
    1: {
        "name": "Accumulation",
        "description": "Smart money quietly buying. Low volume, sideways price.",
        "bias": "BULLISH",
        "color": "#2ecc71",          # Green
        "bg_color": "rgba(46,204,113,0.10)",
        "icon": "🟢",
    },
    2: {
        "name": "Markup Begin",
        "description": "Breakout triggers. Rising volume, price above 20 EMA.",
        "bias": "BULLISH",
        "color": "#27ae60",          # Dark green
        "bg_color": "rgba(39,174,96,0.10)",
        "icon": "🚀",
    },
    3: {
        "name": "Markup Acceleration",
        "description": "Strong trend. Price above 50 EMA, high volume, strong RSI.",
        "bias": "BULLISH",
        "color": "#00d4aa",          # Teal
        "bg_color": "rgba(0,212,170,0.10)",
        "icon": "📈",
    },
    4: {
        "name": "Distribution",
        "description": "Institutional selling. Price near highs but diverging RSI.",
        "bias": "BEARISH",
        "color": "#f39c12",          # Orange
        "bg_color": "rgba(243,156,18,0.10)",
        "icon": "⚠️",
    },
    5: {
        "name": "Markdown Begin",
        "description": "Breakdown. Price below 20 EMA, RSI below 50.",
        "bias": "BEARISH",
        "color": "#e74c3c",          # Red
        "bg_color": "rgba(231,76,60,0.10)",
        "icon": "📉",
    },
    6: {
        "name": "Capitulation",
        "description": "Panic selling. Price far below MA, extreme oversold.",
        "bias": "BEARISH",
        "color": "#c0392b",          # Dark red
        "bg_color": "rgba(192,57,43,0.10)",
        "icon": "🔴",
    },
}

# Phase scoring weights — each condition contributes to phase scores
# Format: (condition_key, phase_number, weight)
PHASE_SCORING_RULES = [
    # RSI conditions
    ("rsi_30_45", 1, 3),
    ("rsi_crossing_50_up", 2, 3),
    ("rsi_60_75", 3, 3),
    ("rsi_divergence_bearish", 4, 3),
    ("rsi_below_50", 5, 3),
    ("rsi_below_30", 6, 3),

    # Price vs EMA conditions
    ("price_above_ema20", 2, 2),
    ("price_above_ema20", 3, 2),
    ("price_below_ema20", 1, 1),
    ("price_below_ema20", 5, 2),
    ("price_below_ema20", 6, 2),
    ("price_above_ema50", 3, 2),
    ("price_above_ema50", 4, 1),
    ("price_far_below_emas", 6, 2),

    # Price action
    ("sideways_price", 1, 2),
    ("price_near_highs", 3, 1),
    ("price_near_highs", 4, 2),

    # Volume conditions
    ("low_volume", 1, 2),
    ("low_volume", 4, 2),
    ("high_volume", 2, 2),
    ("high_volume", 3, 2),
    ("high_volume", 5, 2),
    ("high_volume", 6, 3),

    # MACD conditions
    ("macd_bullish_cross", 2, 2),
    ("macd_bullish_cross", 3, 1),
    ("macd_bearish_cross", 4, 2),
    ("macd_bearish_cross", 5, 2),

    # EMA alignment
    ("ema9_above_ema20", 2, 1),
    ("ema9_above_ema20", 3, 1),
    ("ema9_below_ema20", 5, 1),
    ("ema9_below_ema20", 6, 1),
]

# Maximum possible score per phase (for confidence calculation)
MAX_PHASE_SCORES = {1: 10, 2: 10, 3: 12, 4: 10, 5: 10, 6: 11}

# ──────────────────────────────────────────────
# PREDICTOR SETTINGS
# ──────────────────────────────────────────────
SIGNAL_STRENGTH_THRESHOLDS = {
    "STRONG": 75,
    "MODERATE": 50,
    "WEAK": 0,
}

# VIX thresholds
VIX_CAUTION = 20
VIX_HIGH_RISK = 25
VIX_DEFAULT = 14.0  # Fallback if VIX fetch fails

# PCR interpretation
PCR_BULLISH = 0.7    # PCR > 0.7 → more puts → bullish sentiment
PCR_BEARISH = 1.3    # PCR > 1.3 → extreme puts → potential reversal
PCR_DEFAULT = 1.0    # Fallback

# ──────────────────────────────────────────────
# OPTIONS STRATEGY MATRIX
# ──────────────────────────────────────────────
# (bias, vix_level) → strategy
OPTIONS_STRATEGIES = {
    ("BULLISH", "LOW"):    "Bull Call Spread",
    ("BULLISH", "MEDIUM"): "Long Call",
    ("BULLISH", "HIGH"):   "Bull Put Spread (Sell Put)",
    ("BEARISH", "LOW"):    "Bear Put Spread",
    ("BEARISH", "MEDIUM"): "Long Put",
    ("BEARISH", "HIGH"):   "Bear Call Spread (Sell Call)",
    ("SIDEWAYS", "LOW"):   "Long Straddle",
    ("SIDEWAYS", "MEDIUM"):"Iron Condor",
    ("SIDEWAYS", "HIGH"):  "Short Straddle",
}

# ──────────────────────────────────────────────
# BACKTESTER SETTINGS
# ──────────────────────────────────────────────
BACKTEST_DEFAULT_PERIOD = "2y"  # 2 years of data
RISK_FREE_RATE = 0.065          # India 10Y bond yield approx

# ──────────────────────────────────────────────
# UI CONSTANTS
# ──────────────────────────────────────────────
PHASE_COLORS_PLOTLY = {
    1: "#2ecc71",
    2: "#27ae60",
    3: "#00d4aa",
    4: "#f39c12",
    5: "#e74c3c",
    6: "#c0392b",
}

BULLISH_COLOR = "#00d4aa"
BEARISH_COLOR = "#e74c3c"
NEUTRAL_COLOR = "#f39c12"
CARD_BG = "#1a1f2e"
CARD_BORDER = "#2d3548"
