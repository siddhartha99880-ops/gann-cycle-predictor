"""
database.py — SQLite persistence layer
Stores signal history, backtest results, and alert logs.
"""

import os
import sqlite3
import json
from datetime import datetime

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "gann_cycle.db"
)


def _ensure_db_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection, creating tables if needed."""
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection):
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            phase INTEGER NOT NULL,
            phase_name TEXT NOT NULL,
            phase_confidence REAL,
            directional_bias TEXT,
            signal_strength TEXT,
            entry_zone TEXT,
            targets TEXT,
            stop_loss REAL,
            risk_reward TEXT,
            pcr REAL,
            india_vix REAL,
            oi_signal TEXT,
            fii_activity TEXT,
            options_suggestion TEXT,
            alert_text TEXT,
            raw_json TEXT
        );

        CREATE TABLE IF NOT EXISTS backtest_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            total_trades INTEGER,
            win_rate REAL,
            avg_return REAL,
            max_drawdown REAL,
            sharpe_ratio REAL,
            total_return REAL,
            trade_log TEXT,
            equity_curve TEXT
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            acknowledged INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol, timestamp);
        CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON alerts(symbol, timestamp);
    """)
    conn.commit()


def save_signal(signal_dict: dict):
    """Save a prediction signal to the database."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO signals (timestamp, symbol, timeframe, phase, phase_name,
                phase_confidence, directional_bias, signal_strength, entry_zone,
                targets, stop_loss, risk_reward, pcr, india_vix, oi_signal,
                fii_activity, options_suggestion, alert_text, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            signal_dict.get("symbol", ""),
            signal_dict.get("timeframe", ""),
            signal_dict.get("gyan_cycle_phase", 0),
            signal_dict.get("phase_name", ""),
            signal_dict.get("phase_confidence", 0),
            signal_dict.get("directional_bias", ""),
            signal_dict.get("signal_strength", ""),
            json.dumps(signal_dict.get("entry_zone", [])),
            json.dumps(signal_dict.get("targets", [])),
            signal_dict.get("stop_loss", 0),
            signal_dict.get("risk_reward", ""),
            signal_dict.get("pcr", 0),
            signal_dict.get("india_vix", 0),
            signal_dict.get("oi_signal", ""),
            signal_dict.get("fii_activity", ""),
            signal_dict.get("options_suggestion", ""),
            signal_dict.get("alert", ""),
            json.dumps(signal_dict),
        ))
        conn.commit()
    finally:
        conn.close()


def get_signal_history(symbol: str, limit: int = 50) -> list:
    """Retrieve recent signals for a symbol."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT * FROM signals WHERE symbol = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (symbol, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def save_backtest_result(result: dict):
    """Save backtest results to the database."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO backtest_results (timestamp, symbol, timeframe,
                start_date, end_date, total_trades, win_rate, avg_return,
                max_drawdown, sharpe_ratio, total_return, trade_log, equity_curve)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            result.get("symbol", ""),
            result.get("timeframe", ""),
            result.get("start_date", ""),
            result.get("end_date", ""),
            result.get("total_trades", 0),
            result.get("win_rate", 0),
            result.get("avg_return", 0),
            result.get("max_drawdown", 0),
            result.get("sharpe_ratio", 0),
            result.get("total_return", 0),
            json.dumps(result.get("trade_log", [])),
            json.dumps(result.get("equity_curve", [])),
        ))
        conn.commit()
    finally:
        conn.close()


def save_alert(symbol: str, alert_type: str, severity: str, message: str):
    """Save an alert to the database."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO alerts (timestamp, symbol, alert_type, severity, message)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), symbol, alert_type, severity, message))
        conn.commit()
    finally:
        conn.close()


def get_recent_alerts(limit: int = 20) -> list:
    """Get most recent alerts across all symbols."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def acknowledge_alert(alert_id: int):
    """Mark an alert as acknowledged."""
    conn = get_connection()
    try:
        conn.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
        conn.commit()
    finally:
        conn.close()
