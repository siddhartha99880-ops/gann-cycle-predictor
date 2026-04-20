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

# True Gann Mathematical Conditions
PHASE_SCORING_RULES = [
    # Accumulation (Consolidation near Gann Support)
    ("near_gann_support", 1, 4),
    ("below_gann_1x1", 1, 2),
    ("price_sideways", 1, 4),

    # Markup Begin (Breaking above 1x2 or 1x1)
    ("above_gann_1x2", 2, 4),
    ("breaking_sq9_res", 2, 3),
    ("bullish_time_cycle", 2, 3),

    # Markup Acceleration (Strongly above 1x1)
    ("above_gann_1x1", 3, 5),
    ("cleared_sq9_res", 3, 4),
    ("strong_momentum", 3, 3),

    # Distribution (Stalling near major Sq9 Resistance)
    ("near_gann_resistance", 4, 4),
    ("bearish_time_cycle", 4, 3),
    ("losing_momentum", 4, 3),

    # Markdown Begin (Breaking below 1x1)
    ("below_gann_1x1", 5, 4),
    ("breaking_sq9_sup", 5, 3),
    ("bearish_time_cycle_active", 5, 3),

    # Capitulation (Breaking below 1x2 & dropping hard)
    ("below_gann_1x2_bear", 6, 5),
    ("cleared_sq9_sup", 6, 3),
    ("extreme_down_momentum", 6, 3),
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
