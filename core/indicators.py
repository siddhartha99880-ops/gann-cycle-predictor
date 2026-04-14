"""
indicators.py — Technical indicator calculations
Uses pandas_ta for EMA, RSI, MACD and custom logic for volume ratio & divergence.
All functions append columns to the DataFrame for downstream use.
"""

import pandas as pd
import numpy as np

try:
    import pandas_ta as ta
except ImportError:
    ta = None


def calculate_emas(df: pd.DataFrame, lengths: list = None) -> pd.DataFrame:
    """
    Calculate Exponential Moving Averages for given lengths.
    Appends columns like EMA_9, EMA_20, EMA_50, EMA_200.
    """
    if lengths is None:
        lengths = [9, 20, 50, 200]

    for length in lengths:
        col_name = f"EMA_{length}"
        if ta:
            df[col_name] = ta.ema(df["Close"], length=length)
        else:
            df[col_name] = df["Close"].ewm(span=length, adjust=False).mean()
    return df


def calculate_rsi(df: pd.DataFrame, length: int = 14) -> pd.DataFrame:
    """
    Calculate Relative Strength Index (RSI).
    Appends 'RSI' column.
    """
    if ta:
        df["RSI"] = ta.rsi(df["Close"], length=length)
    else:
        # Manual RSI calculation
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.ewm(com=length - 1, min_periods=length).mean()
        avg_loss = loss.ewm(com=length - 1, min_periods=length).mean()
        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))
    return df


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26,
                   signal: int = 9) -> pd.DataFrame:
    """
    Calculate MACD line, signal line, and histogram.
    Appends 'MACD', 'MACD_Signal', 'MACD_Hist' columns.
    """
    if ta:
        macd_df = ta.macd(df["Close"], fast=fast, slow=slow, signal=signal)
        if macd_df is not None and not macd_df.empty:
            df["MACD"] = macd_df.iloc[:, 0]
            df["MACD_Hist"] = macd_df.iloc[:, 1]
            df["MACD_Signal"] = macd_df.iloc[:, 2]
        else:
            _manual_macd(df, fast, slow, signal)
    else:
        _manual_macd(df, fast, slow, signal)
    return df


def _manual_macd(df, fast, slow, signal):
    """Fallback manual MACD calculation."""
    ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]


def calculate_atr(df: pd.DataFrame, length: int = 14) -> pd.DataFrame:
    """
    Calculate Average True Range (ATR).
    Appends 'ATR' column.
    """
    if ta:
        df["ATR"] = ta.atr(df["High"], df["Low"], df["Close"], length=length)
    else:
        high_low = df["High"] - df["Low"]
        high_close = (df["High"] - df["Close"].shift(1)).abs()
        low_close = (df["Low"] - df["Close"].shift(1)).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["ATR"] = true_range.rolling(window=length).mean()
    return df


def calculate_volume_ratio(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    Calculate volume ratio: current volume / 20-bar average volume.
    Appends 'Volume_Ratio' column.
    Values > 1.2 = high volume; < 0.8 = low volume.
    """
    avg_vol = df["Volume"].rolling(window=period).mean()
    df["Volume_Ratio"] = df["Volume"] / avg_vol
    df["Volume_Ratio"] = df["Volume_Ratio"].replace([np.inf, -np.inf], 1.0).fillna(1.0)
    return df


def detect_rsi_divergence(df: pd.DataFrame, lookback: int = 14) -> pd.DataFrame:
    """
    Detect RSI divergence:
    - Bearish divergence: Price making higher high, RSI making lower high
    - Bullish divergence: Price making lower low, RSI making higher low

    Appends 'RSI_Div_Bearish' and 'RSI_Div_Bullish' boolean columns.
    """
    df["RSI_Div_Bearish"] = False
    df["RSI_Div_Bullish"] = False

    if "RSI" not in df.columns or len(df) < lookback * 2:
        return df

    for i in range(lookback, len(df)):
        window_price = df["Close"].iloc[i - lookback:i + 1]
        window_rsi = df["RSI"].iloc[i - lookback:i + 1]

        if window_rsi.isna().any():
            continue

        # Bearish: price higher high but RSI lower high
        price_curr_high = window_price.iloc[-1]
        price_prev_high = window_price.iloc[:-1].max()
        rsi_curr = window_rsi.iloc[-1]
        rsi_prev_high = window_rsi.iloc[:-1].max()

        if price_curr_high > price_prev_high and rsi_curr < rsi_prev_high:
            df.iloc[i, df.columns.get_loc("RSI_Div_Bearish")] = True

        # Bullish: price lower low but RSI higher low
        price_curr_low = window_price.iloc[-1]
        price_prev_low = window_price.iloc[:-1].min()
        rsi_curr_low = window_rsi.iloc[-1]
        rsi_prev_low = window_rsi.iloc[:-1].min()

        if price_curr_low < price_prev_low and rsi_curr_low > rsi_prev_low:
            df.iloc[i, df.columns.get_loc("RSI_Div_Bullish")] = True

    return df


def price_vs_emas(df: pd.DataFrame) -> dict:
    """
    Check current price position relative to key EMAs.
    Returns dict of booleans for the latest bar.
    """
    if len(df) == 0:
        return {}

    latest = df.iloc[-1]
    close = latest["Close"]

    result = {}
    for ema_len in [9, 20, 50, 200]:
        col = f"EMA_{ema_len}"
        if col in df.columns and not pd.isna(latest.get(col)):
            result[f"above_ema{ema_len}"] = close > latest[col]
            result[f"ema{ema_len}_val"] = latest[col]
        else:
            result[f"above_ema{ema_len}"] = None
            result[f"ema{ema_len}_val"] = None

    return result


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all technical indicators at once.
    This is the main entry point for the indicator module.
    """
    df = calculate_emas(df)
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_atr(df)
    df = calculate_volume_ratio(df)
    df = detect_rsi_divergence(df)
    return df
