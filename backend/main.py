"""
main.py — FastAPI Backend for Gann Cycle Predictor
Exposes REST endpoints for all prediction, analysis, backtest, and alert features.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SYMBOL_MAP, TIMEFRAMES, PHASES, INDEX_SYMBOLS, PHASE_COLORS_PLOTLY
from core.predictor import generate_prediction
from core.gann_cycle import run_multi_timeframe, run_single_timeframe
from core.backtester import run_backtest
from core.alerts import run_all_checks
from core.database import save_signal, get_recent_alerts, save_alert
from core.signals import format_signal_card

# ────────────────────────────────────────
# APP SETUP
# ────────────────────────────────────────
app = FastAPI(
    title="Gann Cycle Predictor API",
    description="Indian Stock Market Futures Prediction Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session state for phase tracking (in-memory)
_prev_phases = {}


# ────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────
def _sanitize(obj):
    """Recursively convert numpy/pandas types to native Python for JSON serialization."""
    if obj is None:
        return None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    if isinstance(obj, (pd.DataFrame, pd.Series)):
        return None
    if isinstance(obj, float) and (pd.isna(obj) or np.isnan(obj)):
        return None
    if isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(i) for i in obj]
    return obj


def _serialize_prediction(prediction: dict) -> dict:
    """Convert prediction dict to JSON-safe format (remove DataFrames)."""
    result = {}
    for k, v in prediction.items():
        if isinstance(v, pd.DataFrame):
            continue  # Skip DataFrames — we handle OHLCV separately
        result[k] = v
    return _sanitize(result)


def _df_to_ohlcv(prediction: dict) -> list:
    """Extract OHLCV data from prediction for frontend charting."""
    df = prediction.get("df", pd.DataFrame())
    if df.empty:
        return []

    chart_df = df.tail(200).copy()
    records = []
    for idx, row in chart_df.iterrows():
        rec = {
            "date": str(idx),
            "open": round(float(row["Open"]), 2) if pd.notna(row.get("Open")) else None,
            "high": round(float(row["High"]), 2) if pd.notna(row.get("High")) else None,
            "low": round(float(row["Low"]), 2) if pd.notna(row.get("Low")) else None,
            "close": round(float(row["Close"]), 2) if pd.notna(row.get("Close")) else None,
            "volume": int(row["Volume"]) if pd.notna(row.get("Volume")) else 0,
        }
        # Add EMAs if available
        for ema in ["EMA_9", "EMA_20", "EMA_50", "EMA_200"]:
            if ema in row and pd.notna(row[ema]):
                rec[ema.lower()] = round(float(row[ema]), 2)
        # Add RSI
        if "RSI" in row and pd.notna(row["RSI"]):
            rec["rsi"] = round(float(row["RSI"]), 2)
        records.append(rec)
    return records


# ────────────────────────────────────────
# ENDPOINTS
# ────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "gann-cycle-predictor", "timestamp": datetime.now().isoformat()}


@app.get("/api/symbols")
def get_symbols():
    """Return available symbols and timeframes."""
    return {
        "symbols": list(SYMBOL_MAP.keys()),
        "timeframes": {k: v["label"] for k, v in TIMEFRAMES.items()},
        "index_symbols": list(INDEX_SYMBOLS.keys()),
    }


@app.get("/api/config")
def get_config():
    """Return phase definitions and UI config."""
    return {
        "phases": {
            str(k): {
                "name": v["name"],
                "description": v["description"],
                "bias": v["bias"],
                "color": v["color"],
                "bg_color": v["bg_color"],
                "icon": v["icon"],
            }
            for k, v in PHASES.items()
        },
        "phase_colors": {str(k): v for k, v in PHASE_COLORS_PLOTLY.items()},
    }


@app.get("/api/prediction")
def get_prediction(
    symbol: str = Query("NIFTY 50", description="Symbol name"),
    timeframe: str = Query("1d", description="Timeframe key"),
):
    """Generate full prediction with Gann Cycle phase detection."""
    global _prev_phases

    try:
        prediction = generate_prediction(symbol, timeframe)

        # Run alert checks
        prev_phase = _prev_phases.get(symbol)
        alerts = run_all_checks(symbol, prev_phase, prediction)
        _prev_phases[symbol] = prediction.get("gann_cycle_phase", 0)

        # Save to DB (silently)
        try:
            save_pred = {k: v for k, v in prediction.items() if not isinstance(v, pd.DataFrame)}
            save_pred.pop("cycle_result", None)
            save_pred.pop("market_data", None)
            save_pred.pop("confluence", None)
            save_signal(save_pred)
        except Exception:
            pass

        # Build response
        ohlcv = _df_to_ohlcv(prediction)
        signal_card = _sanitize(format_signal_card(prediction))
        cycle_result = prediction.get("cycle_result", {})
        scores = cycle_result.get("scores", {})

        # Extract key metrics from DataFrame
        df = prediction.get("df", pd.DataFrame())
        close = prev_close = change = change_pct = 0
        if not df.empty:
            close = float(df["Close"].iloc[-1])
            prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else close
            change = close - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0

        response = _serialize_prediction(prediction)
        response["ohlcv"] = ohlcv
        response["signal_card"] = signal_card
        response["phase_scores"] = _sanitize({str(k): v for k, v in scores.items()}) if scores else {}
        response["price"] = round(close, 2)
        response["price_change"] = round(change, 2)
        response["price_change_pct"] = round(change_pct, 2)
        response["alerts"] = [_sanitize(a.to_dict()) for a in alerts] if alerts else []

        return JSONResponse(content=response)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/multi-timeframe")
def get_multi_timeframe(
    symbol: str = Query("NIFTY 50", description="Symbol name"),
):
    """Run multi-timeframe Gann Cycle analysis."""
    mtf_data = run_multi_timeframe(symbol)
    results = mtf_data.get("results", {})
    confluence = mtf_data.get("confluence", {})

    # Serialize results (remove DataFrames)
    serialized_results = {}
    for tf_key, res in results.items():
        tf_label = TIMEFRAMES.get(tf_key, {}).get("label", tf_key)
        serialized_results[tf_key] = {
            "timeframe_label": tf_label,
            "phase": res.get("phase", 0),
            "phase_name": res.get("phase_name", "N/A"),
            "confidence": round(res.get("confidence", 0), 1),
            "bias": res.get("bias", "SIDEWAYS"),
            "duration": res.get("duration", 0),
            "next_phase_name": res.get("next_phase_name", "N/A"),
            "color": res.get("color", "#888"),
            "icon": res.get("icon", "⚪"),
        }

    return {
        "symbol": symbol,
        "results": serialized_results,
        "confluence": confluence,
    }


class BacktestRequest(BaseModel):
    symbol: str = "NIFTY 50"
    start_date: str = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    end_date: str = datetime.now().strftime("%Y-%m-%d")


@app.post("/api/backtest")
def run_backtest_endpoint(req: BacktestRequest):
    """Run Gann Cycle backtest on historical data."""
    try:
        result = run_backtest(req.symbol, req.start_date, req.end_date)

        # Save to DB
        try:
            from core.database import save_backtest_result
            save_backtest_result(result)
        except Exception:
            pass

        return _sanitize(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/heatmap")
def get_heatmap():
    """Get Gann Cycle phase for all index symbols (sector heatmap)."""
    index_results = {}
    for idx_name in INDEX_SYMBOLS.keys():
        try:
            res = run_single_timeframe(idx_name, "1d")
            if res.get("phase", 0) > 0:
                index_results[idx_name] = {
                    "phase": res.get("phase", 0),
                    "phase_name": res.get("phase_name", "N/A"),
                    "confidence": round(res.get("confidence", 0), 1),
                    "bias": res.get("bias", "SIDEWAYS"),
                    "color": res.get("color", "#888"),
                    "icon": res.get("icon", "⚪"),
                    "duration": res.get("duration", 0),
                    "next_phase_name": res.get("next_phase_name", "N/A"),
                }
        except Exception:
            pass

    # Phase distribution
    phase_counts = {}
    for res in index_results.values():
        p = res["phase"]
        phase_counts[p] = phase_counts.get(p, 0) + 1

    return {
        "indices": index_results,
        "phase_distribution": phase_counts,
        "total": len(index_results),
    }


@app.get("/api/alerts")
def get_alerts(limit: int = Query(30, description="Number of alerts to fetch")):
    """Get recent alert history."""
    try:
        alerts = get_recent_alerts(limit=limit)
        return {"alerts": alerts, "total": len(alerts)}
    except Exception as e:
        return {"alerts": [], "total": 0, "error": str(e)}
