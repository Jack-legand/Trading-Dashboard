# NIFTY Backtest & Classification

This repository contains a Python script `backtest_nifty.py` that processes daily OHLC data for NIFTY 50 and produces aggregated statistics used for a Streamlit dashboard.

Files added:
- `backtest_nifty.py` — main script to compute CPR, candle states, open contexts, next-day outcomes, and gap analysis. Produces CSV outputs.
- `requirements.txt` — Python dependencies.

Quick start

1. Install dependencies (preferably in a virtualenv):

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

2. Place your Excel/CSV file (matching the expected columns) in the repository root. Example filename used in development: `Nifty Data.xlsx`.

3. Run the script (outputs written to `data/` by default):

```bash
python3 backtest_nifty.py --input "Nifty Data.xlsx" --output data
ls -lah data
```

Outputs

- `data/candle_state_stats.csv`
- `data/open_context_stats.csv`
- `data/gap_stats.csv`

Notes and assumptions
- The script auto-detects Open/High/Low/Close columns by substring matching. If column names differ, rename columns to include the words "Open", "High", "Low", and "Close".
- Date parsing assumes day-first format; adjust if needed.
- The script handles missing/insufficient history by using sensible defaults (e.g., `Balanced_Neutral`).

Want me to run the script here and save CSVs into `data/`? If you want that, grant file access or run the commands above in your environment.
# Trading-Dashboard
Used for trading Nifty Options intraday
