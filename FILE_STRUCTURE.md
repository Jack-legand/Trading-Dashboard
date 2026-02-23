# 📁 File Structure & Inventory - v2.1

Complete file-by-file breakdown of the NIFTY Edge Dashboard.

## 📂 Root Level Files

### Application Files

#### `app.py` (679 lines)
**Purpose**: Main Streamlit dashboard application

**Functions**:
- Load session cache and backtested statistics
- Welcome page: Input OHLC and calculate edges
- Edge detection: Display three games with probabilities
- Trade logging: Record trades with discipline tracking
- Insights: Analyze performance and discipline

**Key Functions**:
- `compute_cpr()` - Calculates corrected CPR levels
- `bucket_gap()` - Assigns gap to percentage bucket
- `welcome_page()` - User input and edge calculation
- `edge_detection_page()` - Three games display
- `trade_logging_page()` - Trade entry form
- `insight_page()` - Performance analytics

**Dependencies**: pandas, streamlit, plotly

#### `backtest_nifty.py` (432 lines)
**Purpose**: Backtesting engine that generates statistics

**Functions**:
- Load OHLC data from Excel or CSV
- Compute CPR levels with corrected formula
- Classify candle states using body % thresholds
- Classify open context relative to range and CPR
- Label next-day outcomes
- Analyze gap fills
- Aggregate and write statistics

**Key Functions**:
- `compute_cpr()` - Correct CPR formula with TC/BC swap
- `classify_previous_candle()` - Body/wick percentile analysis
- `classify_open_context()` - Range and CPR positioning
- `label_next_day_outcomes()` - Trend and break classification
- `gap_analysis()` - Gap fill probability calculation
- `aggregate_and_write()` - Write CSV outputs

**Dependencies**: pandas, numpy, openpyxl, argparse

### Configuration Files

#### `requirements.txt`
Python package dependencies:
- pandas: Data manipulation
- numpy: Numerical operations
- openpyxl: Excel file reading
- plotly: Interactive visualizations
- streamlit: Dashboard framework

#### `runtime.txt`
Python runtime specification for deployment
- Python 3.10 or compatible

### Data Files

#### `Nifty Data.xlsx`
Historical NIFTY OHLC data with columns:
- Date (day-first format)
- Open
- High  
- Low
- Close

Used as input for backtesting.

---

## 📂 `/data` Directory

Generated files from backtesting (automatically created):

#### `candle_state_stats.csv`
**Columns**: 
- candle_state: Classification (Strong_Acceptance, Exhaustion_Rejection, etc.)
- total_count: Number of occurrences
- prob_trend_up: Probability of next day trend up
- prob_trend_down: Probability of next day trend down
- prob_range_chop: Probability of sideways/chop
- avg_next_day_range_pct: Average range expansion percentage

**Usage**: Candle Structure Game

#### `open_context_stats.csv`
**Columns**:
- open_context: Classification (Open position + CPR position + Quartile)
- total_count: Number of occurrences
- prob_trend_up: Probability of next day trend up
- prob_trend_down: Probability of next day trend down
- prob_range_chop: Probability of sideways
- prob_pdh_break_success: % of PDH breaks that hold
- prob_pdl_break_success: % of PDL breaks that hold
- prob_false_pdh_break: % of false PDH breaks
- prob_false_pdl_break: % of false PDL breaks
- avg_next_day_range_pct: Average range expansion

**Usage**: Level Game

#### `gap_stats.csv` (v2.1 - Corrected)
**Columns**:
- gap_direction: Gap_Up, Gap_Down, or No_Gap
- gap_bucket: 0-0.5%, 0.5-1%, 1-2%, >2%
- total_count: Number of occurrences
- prob_fill_50pct: Probability gap filled by 50%
- prob_fill_80pct: Probability gap filled by 80%
- prob_fill_100pct: Probability gap completely filled
- avg_gap_size_pct: Average gap percentage in bucket

**Usage**: Gap Game
**Note**: v2.1 corrected - Gap % = |Open - Prev Close| / Prev Close

#### `thresholds.json`
Global thresholds for candle classification:
```json
{
  "body_70": 0.65,
  "body_30": 0.15
}
```

70th and 30th percentiles of body % used for Strong/Weak candle classification.

#### `.session_cache.json`  (Runtime)
Persistent session data storing:
- Last input values (prev_open, prev_high, prev_low, prev_close, today_open)
- Last calculated edge results
- Last selected test date

Automatically created and updated by app.py

#### `trade_log.csv` (Runtime)
Trade execution log appended by Trade Logging page:

**Columns**:
- timestamp: When trade was logged
- edge_type: Structural/Level/Gap edge
- market_direction: Expected direction
- harmony: Yes/No for risk alignment
- entry_price: Entry level
- stop_loss: Risk control level
- num_lots: Position size in lots
- qty_per_lot: Quantity per lot
- instrument: Call/Put option
- pre_trade_data_flag: Yes/No
- exit_price: Exit level (if closed)
- charges: Transaction costs (if applicable)
- exit_reason: SL hit / Target / Manual / Time
- trade_date: Trade execution date
- risk_amount: Calculated risk = |Entry - SL| × Qty × Lots

---

## 📄 Documentation Files

#### `README.md`
Quick start guide with:
- System overview
- Installation instructions
- Quick run commands
- Core formula summaries
- Links to detailed docs

**Audience**: New users, quick reference

#### `INDEX.md`
Detailed feature documentation with:
- Three games descriptions
- Page-by-page guide
- Calculation methods
- Workflow instructions

**Audience**: Feature understanding and usage

#### `FILE_STRUCTURE.md` (This File)
Complete file inventory with:
- Purpose of each file
- Column descriptions for CSVs
- Function listings
- Usage patterns

**Audience**: Technical reference

#### `CHANGELOG.md`
Version history with:
- v2.1: Current improvements
- v2.0: Previous features
- v1.0: Initial release
- Detailed change notes for each version

**Audience**: Users tracking changes

---

## 🗑️ Removed in v2.1

The following files were removed to clean up the repository (noise/duplicates):

- `app_new.py` - Alternative version (superseded by app.py)
- `ARCHITECTURE.md` - Replaced by INDEX.md
- `COMPLETION_REPORT.md` - Redundant documentation
- `FINAL_SUMMARY.md` - Redundant documentation
- `IMPROVEMENTS.md` - Redundant documentation
- `QUICKSTART.md` - Content merged into README.md
- `START_HERE.md` - Content merged into README.md
- `SUCCESS.md` - Redundant
- `SUMMARY.md` - Redundant
- `complete_backtest_and_push.py` - Helper script
- `execute_backtest.py` - Helper script
- `git_workflow.py` - Helper script
- `push_changes.sh` - Helper script
- `run_backtest_and_push.py` - Helper script
- `imghdr.py` - Unused module
- `imghdr_pkg/` - Unused package

**Result**: Clean, focused repository with only essential files.

---

## 📋 Directory Structure Summary

```
Trading-Dashboard/
├── app.py                          # Main dashboard
├── backtest_nifty.py              # Backtesting engine
├── requirements.txt                # Dependencies
├── runtime.txt                     # Runtime specification
├── Nifty Data.xlsx                # Historical data
│
├── README.md                       # Quick start
├── INDEX.md                        # Feature documentation
├── FILE_STRUCTURE.md              # This file
├── CHANGELOG.md                    # Version history
│
├── data/                           # Generated files
│   ├── candle_state_stats.csv
│   ├── open_context_stats.csv
│   ├── gap_stats.csv
│   ├── thresholds.json
│   ├── .session_cache.json        # Runtime
│   └── trade_log.csv              # Runtime
│
├── .git/                          # Git repository
└── __pycache__/                   # Python cache (auto)
```

---

## 🚀 Workflow File Usage

### Running Backtest
```bash
python backtest_nifty.py \
  --input "Nifty Data.xlsx" \
  --output data/
```

**Reads**: `Nifty Data.xlsx`
**Writes**: 
- `data/candle_state_stats.csv`
- `data/open_context_stats.csv`
- `data/gap_stats.csv`
- `data/thresholds.json`

### Running Dashboard
```bash
streamlit run app.py
```

**Reads**:
- `data/candle_state_stats.csv`
- `data/open_context_stats.csv`
- `data/gap_stats.csv`
- `data/thresholds.json` (for candle classification)
- `data/.session_cache.json` (loads last inputs)
- `Nifty Data.xlsx` (optional - for historical check)

**Writes**:
- `data/.session_cache.json` (saves current inputs)
- `data/trade_log.csv` (appends trade entries)

---

## 📊 File Size Reference

| File | Size | Type |
|------|------|------|
| app.py | ~22 KB | Code |
| backtest_nifty.py | ~14 KB | Code |
| Nifty Data.xlsx | ~1-5 MB | Data |
| candle_state_stats.csv | ~5-50 KB | Stats |
| open_context_stats.csv | ~10-100 KB | Stats |
| gap_stats.csv | ~2-10 KB | Stats |
| thresholds.json | <1 KB | Config |
| trade_log.csv | Grows per trade | Log |

---

**Version**: 2.1  
**Last Updated**: February 23, 2026
