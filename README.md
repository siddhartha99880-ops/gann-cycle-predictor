# Gann Cycle Predictor

⚡ **Indian Stock Market Futures Prediction Engine** — powered by W.D. Gann's cyclical market model.

## Architecture

| Component | Stack | Deployed On |
|---|---|---|
| **Backend** | FastAPI + Python (yfinance, pandas-ta) | Railway |
| **Frontend** | Vanilla HTML/CSS/JS + Plotly.js | Vercel |

## Features

- 📊 **6-Phase Gann Cycle Detection** — Accumulation → Markup → Distribution → Capitulation
- 🔄 **Multi-Timeframe Analysis** — 5m, 15m, 1h, Daily, Weekly confluence
- 📈 **Backtester** — Historical signal performance with equity curves
- 🗺️ **Sector Heatmap** — Phase detection across NIFTY, Bank NIFTY, SENSEX
- 🔔 **Smart Alerts** — Phase transitions, RSI divergences, VIX spikes
- 📡 **Live Market Sentiment** — PCR, Open Interest, VIX, FII/DII

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
# Serve with any static server
npx serve .
# or just open index.html in browser
```

## Data Sources
- Yahoo Finance (yfinance)
- NSE India (derivatives data)

---

> ⚠️ **Disclaimer**: For educational & analysis purposes only. Not financial advice. Always do your own research.
