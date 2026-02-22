# 🚀 Quick Start Guide - NIFTY Edge Dashboard v2.0

## Installation & Setup

### Prerequisites
- Python 3.8+ 
- Access to `/workspaces/Trading-Dashboard/` directory
- NIFTY daily OHLC data in `Nifty Data.xlsx` or `Nifty Data.csv`

### Step 1: Install Dependencies
```bash
cd /workspaces/Trading-Dashboard
pip install -r requirements.txt
```

**Required packages**:
- streamlit
- pandas
- numpy
- openpyxl
- plotly

### Step 2: Prepare Data
Ensure you have `Nifty Data.xlsx` with:
- **Row 3** containing headers: Date, Year, Month, Day, Open_Nifty, High_Nifty, Low_Nifty, Close_Nifty, Open_VIX, ...
- **Row 4 onwards** containing daily OHLC data

### Step 3: Run Backtest (One-time Setup)
```bash
python3 backtest_nifty.py --input "Nifty Data.xlsx" --output data --header-row 3
```

This generates:
- `data/candle_state_stats.csv` - Candle classification probabilities
- `data/open_context_stats.csv` - Open level game probabilities  
- `data/gap_stats.csv` - Gap filling statistics
- `data/thresholds.json` - Body percentile thresholds

### Step 4: Launch Dashboard
```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`

---

## Using the Dashboard

### 📍 Welcome Page
1. Enter **Previous Day OHLC**:
   - Previous Day Open
   - Previous Day High
   - Previous Day Low
   - Previous Day Close

2. Enter **Today's Open**

3. Select **Test Date** (the date you want to analyze)

4. Click **📊 Calculate Edges**

**What happens**:
- System computes CPR levels (Pivot, Top, Bottom)
- Calculates edge probabilities for all three games
- All inputs saved to `data/.session_cache.json`
- Shows CPR metric cards and historical validation

### 🎯 Edge Detection Page
View three independent trading edges:

#### **🕯️ Candle Structure Game**
- Previous candle's body percentage determines market acceptance
- Green gauges = Bullish probability (next day up)
- Red gauges = Bearish probability (next day down)
- Orange gauges = Sideways probability (range chop)
- Sample size = how many similar candles in historical data

#### **📊 Level Game**
- Today's open relative to PDH/PDL/CPR zones
- Blue gauge = Trend Up probability
- Red gauge = Trend Down probability
- PDH/PDL break success rates shown below

#### **📉 Gap Game**
- Gap from previous close to today's open
- Shows fill probability for 50%, 80%, 100% gaps
- Gray bar = 50% fill likely
- Orange bar = 80% fill likely
- Green bar = 100% fill likely

**Clear Data & Start Over**: Resets all session data for next trading day

### 📝 Trade Logging Page
Record each trade you take:

1. **Edge Type**: Which game triggered this trade?
2. **Market Direction**: Your directional bias (Up/Down/Sideways)
3. **Harmony with Capital**: Is this trade aligned with your rules?
4. **Entry Price**: At what price did you enter?
5. **Stop Loss**: Your risk level
6. **Qty Details**: Number of lots × quantity per lot
7. **Instrument**: Call or Put Option
8. **Pre-trade Data**: Was this trade planned BEFORE taking it? (Critical for discipline!)
9. **Exit Price**: Where did you exit? (optional, can be filled later)
10. **Exit Reason**: SL hit, Target hit, Manual, or Time exit

**Risk Calculation**: Automatically computed as = (Entry - SL) × Quantity × Lots

Click **💾 Save Trade** → Appends to `data/trade_log.csv`

### 📊 Insight Page
Analyze your trading performance:

**Key Metrics** (Top 5 cards):
- **Total P&L**: Cumulative profit/loss in rupees
- **Win Rate**: Percentage of winning trades
- **Avg Risk**: Average rupee risk per trade
- **Profit Factor**: Gross Profit ÷ Gross Loss (>1.5 is good)
- **Discipline 🎯**: % of trades with pre-planned data (Target: 100%)

**Charts**:
- **📈 Equity Curve**: Blue line showing cumulative P&L growth over time
- **📊 Risk Pattern**: Red bars showing risk amount per trade
- **📋 Execution Discipline**: Table of all trades with exit reasons

---

## 📊 Data Persistence

### Session Cache (`data/.session_cache.json`)
- **Auto-created** on first edge calculation
- **Stores**: OHLC inputs, computed edges, test date
- **Restores**: All inputs when you reopen the dashboard
- **Cleared**: Only when you click "Clear Data & Start Over"

**Example**:
```json
{
  "prev_open": 20100.0,
  "prev_high": 20250.0,
  "prev_low": 20050.0,
  "prev_close": 20150.0,
  "today_open": 20180.0,
  "test_date": "2024-01-20",
  "candle_state": "Strong_Acceptance|Close_Near_High",
  "open_context": "Above_CPR",
  "gap_dir": "Gap_Up",
  "gap_bucket": "0.5-1%"
}
```

### Trade Log (`data/trade_log.csv`)
- **Persistent**: Grows with each logged trade
- **Columns**: timestamp, edge_type, entry_price, exit_price, pnl, risk_amount, etc.
- **Used for**: Equity curve, win rate, discipline tracking

---

## 🎨 Color Reference

| Element | Color | Meaning |
|---------|-------|---------|
| Green (#2ecc71) | 🟢 | Bullish, Positive, Long bias |
| Red (#e74c3c) | 🔴 | Bearish, Negative, Short bias |
| Orange (#f39c12) | 🟠 | Neutral, Sideways, Balanced |
| Blue (#3498db) | 🔵 | Information, Analytics |
| Gray (#95a5a6) | ⚫ | Supporting data |

---

## 🗂️ File Structure

```
Trading-Dashboard/
├── app.py                    # Main Streamlit dashboard
├── backtest_nifty.py         # Backtesting engine
├── requirements.txt          # Python dependencies  
├── README.md                 # Original readme
├── IMPROVEMENTS.md           # Detailed feature list
├── Nifty Data.xlsx          # Your OHLC data (in your local system)
└── data/
    ├── candle_state_stats.csv      # From backtest
    ├── open_context_stats.csv      # From backtest
    ├── gap_stats.csv               # From backtest
    ├── thresholds.json             # From backtest
    ├── trade_log.csv               # User-generated
    └── .session_cache.json         # Auto-created (hidden)
```

---

## 🔧 Troubleshooting

### Q: "No edge computed yet" error on Edge Detection page
**A**: Go to Welcome page and click "Calculate Edges" first

### Q: Data disappears when I close the dashboard
**A**: This is normal - close with app.py still running. Data is in `data/.session_cache.json`. Reopen and it will restore.

### Q: Historical validation not showing
**A**: Make sure `Nifty Data.xlsx` or `Nifty Data.csv` exists with historical data. The system will automatically detect and load it.

### Q: Trade logging not working
**A**: Ensure `data/` directory exists. The app will create it automatically, but check write permissions.

### Q: Wrong probabilities displayed
**A**: Rerun the backtesting script with fresh data:
```bash
python3 backtest_nifty.py --input "Nifty Data.xlsx" --output data --header-row 3
```

---

## 📈 Example Trading Flow

**Day 1: Friday Evening**
1. Open dashboard Welcome page
2. Enter Friday's OHLC (e.g., Open: 20100, High: 20250, Low: 20050, Close: 20150)
3. Enter Expected Monday Open: 20180
4. Click "Calculate Edges"
5. Check Edge Detection page → See probabilities for Monday
6. Plan trades based on edge probabilities
7. Close dashboard (data persists in cache)

**Day 2: Monday Morning**
1. Reopen dashboard → Previous OHLC restored automatically
2. View edges computed yesterday
3. As you trade, log each trade in "Trade Logging" page
4. Check "Insight" page for real-time P&L and discipline score
5. Click "Clear Data" when done to reset for next week

---

## 🎯 Tips for Best Results

1. **Pre-plan trades**: Check "Yes" on "Data entered before trade?" for discipline tracking
2. **Log all trades**: Even small ones - needed for accurate statistics  
3. **Use CPR levels**: Set protective stops near BC, targets near TC
4. **Monitor discipline**: Aim for 100% pre-planned trades
5. **Weekly reviews**: Check Insight page on Friday to review performance
6. **Update backtest data**: Run backtest script monthly with fresh data for current probabilities

---

## 📞 Support

- Check `IMPROVEMENTS.md` for detailed feature documentation
- Review `backtest_nifty.py` for backtesting logic
- Ensure Python 3.8+ and all dependencies installed
- Check `data/` folder for generated CSV files

---

**Current Version**: 2.0 Enhanced  
**Last Updated**: January 20, 2024  
**Status**: Production Ready ✅
