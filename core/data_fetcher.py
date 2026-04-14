"""
data_fetcher.py — Data retrieval layer
Fetches OHLCV data from Yahoo Finance (yfinance) for NSE/BSE symbols.
Includes local CSV caching to minimize API calls.
"""

import os
import time
import hashlib
import pandas as pd
import yfinance as yf

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SYMBOL_MAP, TIMEFRAMES, DEFAULT_TIMEFRAME

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CACHE_TTL_SECONDS = 300  # 5 minutes cache TTL


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_key(symbol: str, interval: str, period: str) -> str:
    """Generate a unique cache filename."""
    raw = f"{symbol}_{interval}_{period}"
    return hashlib.md5(raw.encode()).hexdigest() + ".csv"


def _is_cache_valid(filepath: str) -> bool:
    """Check if cached file exists and is within TTL."""
    if not os.path.exists(filepath):
        return False
    age = time.time() - os.path.getmtime(filepath)
    return age < CACHE_TTL_SECONDS


def get_yahoo_symbol(display_name: str) -> str:
    """
    Convert display name to Yahoo Finance ticker symbol.
    e.g., "NIFTY 50" → "^NSEI", "RELIANCE" → "RELIANCE.NS"
    """
    if display_name in SYMBOL_MAP:
        return SYMBOL_MAP[display_name]
    # If not in map, assume it's a stock and append .NS
    return f"{display_name}.NS"


def fetch_ohlcv(symbol: str, period: str = "1y", interval: str = "1d",
                use_cache: bool = True) -> pd.DataFrame:
    """
    Fetch OHLCV data for a given symbol.

    Args:
        symbol: Display name (e.g., "NIFTY 50") or Yahoo symbol
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
        interval: Bar interval (1m, 5m, 15m, 1h, 1d, 1wk, 1mo)
        use_cache: Whether to use local CSV cache

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
    """
    _ensure_cache_dir()

    yahoo_sym = get_yahoo_symbol(symbol) if symbol in SYMBOL_MAP else symbol
    cache_file = os.path.join(CACHE_DIR, _cache_key(yahoo_sym, interval, period))

    # Check cache
    if use_cache and _is_cache_valid(cache_file):
        try:
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            if not df.empty:
                return df
        except Exception:
            pass

    # Fetch from Yahoo Finance
    try:
        ticker = yf.Ticker(yahoo_sym)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            # Try alternative download method
            df = yf.download(yahoo_sym, period=period, interval=interval,
                             progress=False, auto_adjust=True)

        if df.empty:
            return pd.DataFrame()

        # Standardize column names (handle multi-level columns from yf.download)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Ensure we have the expected columns
        expected_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in expected_cols:
            if col not in df.columns:
                # Try case-insensitive match
                for c in df.columns:
                    if c.lower() == col.lower():
                        df.rename(columns={c: col}, inplace=True)
                        break

        # Keep only OHLCV columns
        available = [c for c in expected_cols if c in df.columns]
        df = df[available].copy()

        # Remove timezone info from index if present
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        # Drop NaN rows
        df.dropna(subset=["Close"], inplace=True)

        # Save to cache
        if use_cache and not df.empty:
            try:
                df.to_csv(cache_file)
            except Exception:
                pass

        return df

    except Exception as e:
        print(f"Error fetching data for {yahoo_sym}: {e}")
        return pd.DataFrame()


def fetch_multi_timeframe(symbol: str) -> dict:
    """
    Fetch OHLCV data for all configured timeframes.

    Returns:
        Dict mapping timeframe key to DataFrame.
        e.g., {"5m": df_5m, "15m": df_15m, "1h": df_1h, ...}
    """
    results = {}
    for tf_key, tf_config in TIMEFRAMES.items():
        df = fetch_ohlcv(
            symbol,
            period=tf_config["period"],
            interval=tf_config["interval"]
        )
        if not df.empty:
            results[tf_key] = df
    return results


def fetch_historical(symbol: str, start: str, end: str,
                     interval: str = "1d") -> pd.DataFrame:
    """
    Fetch historical OHLCV data between specific dates.
    Used primarily by the backtester.

    Args:
        symbol: Display name or Yahoo symbol
        start: Start date string (YYYY-MM-DD)
        end: End date string (YYYY-MM-DD)
        interval: Bar interval

    Returns:
        DataFrame with OHLCV data
    """
    yahoo_sym = get_yahoo_symbol(symbol) if symbol in SYMBOL_MAP else symbol

    try:
        df = yf.download(yahoo_sym, start=start, end=end,
                         interval=interval, progress=False, auto_adjust=True)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df.dropna(subset=["Close"], inplace=True)
        return df

    except Exception as e:
        print(f"Error fetching historical data for {yahoo_sym}: {e}")
        return pd.DataFrame()
