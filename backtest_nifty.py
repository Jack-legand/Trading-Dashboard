"""
Backtesting / classification script for NIFTY daily OHLC data.

Usage:
  python backtest_nifty.py --input "/workspaces/Trading-Dashboard/Nifty Data.xlsx" --output data/

The script reads an Excel/CSV file, computes previous-day CPR and candle metrics,
classifies candle states, open contexts, next-day outcomes, gap fills, and
writes multiple CSVs into the output directory:
  - candle_state_stats.csv
  - open_context_stats.csv
  - gap_stats.csv
  - level_game_stats.csv

Defaults are set to the provided file path; adjust CLI args as needed.
"""
import argparse
import os
import sys
from typing import Optional

import numpy as np
import pandas as pd


def find_ohlc_cols(cols: pd.Index):
    # Try to find best-matching names for Open, High, Low, Close columns.
    cols_lower = [c.lower() for c in cols]
    def find(keyword):
        for i, c in enumerate(cols_lower):
            if keyword in c:
                return cols[i]
        return None

    o = find('open')
    h = find('high')
    l = find('low')
    c = find('close')
    return o, h, l, c


def safe_div(a, b):
    return np.where((b == 0) | pd.isna(b), np.nan, a / b)


def classify_previous_candle(df):
    # compute rolling percentiles (20, min 10) on Body% and shift so percentiles
    # represent values up to previous day when classifying "previous day".
    body_pct = df['body_pct_prev']
    p70 = body_pct.rolling(window=20, min_periods=10).quantile(0.7).shift(1)
    p30 = body_pct.rolling(window=20, min_periods=10).quantile(0.3).shift(1)

    states = []
    for idx, row in df.iterrows():
        bp = row['body_pct_prev']
        up = row['upper_wick_pct_prev']
        lo = row['lower_wick_pct_prev']
        wick_imb = row['wick_imbalance_prev']
        top_rej = row['top_rejection_prev']
        bot_rej = row['bottom_rejection_prev']

        # if percentiles are nan (not enough history), default to Balanced_Neutral
        if pd.isna(p70.loc[idx]) or pd.isna(p30.loc[idx]) or pd.isna(bp):
            base = 'Balanced_Neutral'
        else:
            if (bp > p70.loc[idx]) and (up < 0.2) and (lo < 0.2):
                base = 'Strong_Acceptance'
            elif (bp < p30.loc[idx]) and ((up > 0.4) or (lo > 0.4)):
                base = 'Exhaustion_Rejection'
            elif (bp > p70.loc[idx]) and ((up > 0.3) or (lo > 0.3)):
                base = 'Expansion'
            elif (bp < p30.loc[idx]) and (up < 0.3) and (lo < 0.3):
                base = 'Compression'
            else:
                base = 'Balanced_Neutral'

        tags = []
        if not pd.isna(wick_imb):
            if wick_imb > 0.3:
                tags.append('Upper_Wick_Dominant')
            if wick_imb < -0.3:
                tags.append('Lower_Wick_Dominant')
        if not pd.isna(top_rej) and top_rej < 0.2:
            tags.append('Close_Near_High')
        if not pd.isna(bot_rej) and bot_rej < 0.2:
            tags.append('Close_Near_Low')

        state = base
        if tags:
            state = state + '|' + '|'.join(tags)
        states.append(state)

    df['candle_state'] = states


def classify_open_context(df):
    """
    Classify open context relative to previous day's range and CPR.
    
    FIXED: Quartile tags (Open_Top_Quartile, Open_Bottom_Quartile, Open_Middle_Half)
    are now ONLY appended if the open is INSIDE the previous day's range.
    If open is outside the range (Above_PDH or Below_PDL), quartile tags are NOT added
    to match dashboard-compatible strings.
    """
    ctxs = []
    for idx, row in df.iterrows():
        o = row['Open']
        pdh = row['PDH']
        pdl = row['PDL']
        tc = row['TC']
        bc = row['BC']
        prev_range = row['prev_range']

        parts = []
        if pd.isna(o) or pd.isna(pdh) or pd.isna(pdl):
            ctxs.append('Unknown')
            continue

        # Determine if open is inside or outside previous range
        is_inside_range = (o >= pdl) and (o <= pdh)

        # Main open location tags
        if o > pdh:
            parts.append('Open_Above_PDH')
        elif o < pdl:
            parts.append('Open_Below_PDL')
        else:
            parts.append('Open_Inside_Prev_Range')

        # CPR tag
        if not pd.isna(tc) and not pd.isna(bc):
            if o > tc:
                parts.append('Above_CPR')
            elif o < bc:
                parts.append('Below_CPR')
            else:
                parts.append('Inside_CPR')

        # Quartile tags ONLY for inside previous range (dashboard-compatible)
        if is_inside_range:
            if pd.isna(prev_range) or prev_range == 0:
                parts.append('Open_Middle_Half')
            else:
                # top 25%: (PDH - Open)/Range < 0.25
                if (pdh - o) / prev_range < 0.25:
                    parts.append('Open_Top_Quartile')
                elif (o - pdl) / prev_range < 0.25:
                    parts.append('Open_Bottom_Quartile')
                else:
                    parts.append('Open_Middle_Half')
        # NOTE: No quartile tags appended if open is outside range

        ctxs.append('|'.join(parts))

    df['open_context'] = ctxs


def label_next_day_outcomes(df):
    outcomes = []
    expansion_flags = []
    false_pdh = []
    false_pdl = []
    pdh_success = []
    pdl_success = []
    next_range_pct = []

    for idx, row in df.iterrows():
        nh = row.get('next_high')
        nl = row.get('next_low')
        nc = row.get('next_close')
        no = row.get('next_open')
        prev_range = row.get('prev_range')
        pdh = row.get('PDH')
        pdl = row.get('PDL')

        if pd.isna(nh) or pd.isna(nl) or pd.isna(nc) or pd.isna(no):
            outcomes.append(np.nan)
            expansion_flags.append(np.nan)
            false_pdh.append(False)
            false_pdl.append(False)
            pdh_success.append(False)
            pdl_success.append(False)
            next_range_pct.append(np.nan)
            continue

        nrange = nh - nl
        nbody_pct = safe_div(abs(nc - no), nrange)
        parts = []
        if not pd.isna(nbody_pct) and nbody_pct > 0.6 and (nc > no):
            parts.append('Trend_Up_Day')
        elif not pd.isna(nbody_pct) and nbody_pct > 0.6 and (nc < no):
            parts.append('Trend_Down_Day')
        else:
            parts.append('Range_Chop_Day')

        # PDH/PDL breaks
        if (nh > pdh) and (nc < pdh):
            parts.append('False_PDH_Break')
            false_pdh.append(True)
        else:
            false_pdh.append(False)

        if (nl < pdl) and (nc > pdl):
            parts.append('False_PDL_Break')
            false_pdl.append(True)
        else:
            false_pdl.append(False)

        if (nh > pdh) and (nc >= pdh):
            parts.append('PDH_Break_Success')
            pdh_success.append(True)
        else:
            pdh_success.append(False)

        if (nl < pdl) and (nc <= pdl):
            parts.append('PDL_Break_Success')
            pdl_success.append(True)
        else:
            pdl_success.append(False)

        # Range expansion
        if pd.isna(prev_range) or prev_range == 0:
            expansion_flags.append('Normal_Range_Day')
        else:
            if nrange > prev_range * 1.2:
                expansion_flags.append('Expansion_Day')
                parts.append('Expansion_Day')
            else:
                expansion_flags.append('Normal_Range_Day')
                parts.append('Normal_Range_Day')

        outcomes.append('|'.join(parts))
        next_range_pct.append(safe_div(nrange, prev_range))

    df['next_day_outcome'] = outcomes
    df['expansion_flag'] = expansion_flags
    df['false_pdh_break'] = false_pdh
    df['false_pdl_break'] = false_pdl
    df['pdh_break_success'] = pdh_success
    df['pdl_break_success'] = pdl_success
    df['next_range_pct'] = next_range_pct


def gap_analysis(df):
    """
    Analyze gaps formed at today's open and same-day fills.
    
    Gap = Open - prev_close (calculated from today's data)
    Fill probabilities measure whether the gap is filled during the same day's session.
    """
    # gap = Open - prev_close
    gaps = df['Open'] - df['prev_close']
    df['gap'] = gaps
    df['gap_direction'] = np.where(gaps > 0, 'Gap_Up', np.where(gaps < 0, 'Gap_Down', 'No_Gap'))
    df['gap_size_pct'] = safe_div(abs(gaps), df['prev_close'])

    fill50 = []
    fill80 = []
    fill100 = []

    for idx, row in df.iterrows():
        g = row['gap']
        prev_close = row['prev_close']
        low = row['Low']
        high = row['High']
        if pd.isna(g) or pd.isna(prev_close):
            fill50.append(False)
            fill80.append(False)
            fill100.append(False)
            continue

        if g > 0:
            # Gap Up: filled if Low <= prev_close (same-day fill)
            fill100.append(low <= prev_close)
            fill80.append(low <= (prev_close + 0.8 * g))
            fill50.append(low <= (prev_close + 0.5 * g))
        elif g < 0:
            # Gap Down: filled if High >= prev_close (same-day fill)
            ag = abs(g)
            fill100.append(high >= prev_close)
            fill80.append(high >= (prev_close - 0.8 * ag))
            fill50.append(high >= (prev_close - 0.5 * ag))
        else:
            fill50.append(False)
            fill80.append(False)
            fill100.append(False)

    df['fill_50pct'] = fill50
    df['fill_80pct'] = fill80
    df['fill_100pct'] = fill100


def compute_level_game_stats(df, outdir):
    """
    Compute detailed scenario data for the Level Game.
    
    For each key level (PDH, PDL, TC, BC), track:
    - FirstTouch: Whether the level was touched during the day
    - Broken: Whether the level was broken from the open side
    - AfterBreakRetouch: If broken, whether price retouched the level after breaking
    - BreakSuccess: If broken, whether the close was beyond the level (confirming break)
    
    Output: level_game_stats.csv
    """
    stats = []
    
    for idx, row in df.iterrows():
        date = row.get('Date')
        openp = row.get('Open')
        high = row.get('High')
        low = row.get('Low')
        close = row.get('Close')
        pdh = row.get('PDH')
        pdl = row.get('PDL')
        tc = row.get('TC')
        bc = row.get('BC')

        levels = {
            'PDH': pdh,
            'PDL': pdl,
            'TC': tc,
            'BC': bc
        }

        for lvl_name, lvl_val in levels.items():
            if pd.isna(lvl_val) or pd.isna(openp) or pd.isna(high) or pd.isna(low) or pd.isna(close):
                continue

            # FirstTouch: level was touched during the day (high >= lvl and low <= lvl)
            first_touch = (high >= lvl_val) and (low <= lvl_val)

            # Broken: level was crossed from the open side
            if openp < lvl_val:
                # Open is below level; broken if high crosses above
                broken = high > lvl_val
                broken_direction = 'Up'
            elif openp > lvl_val:
                # Open is above level; broken if low crosses below
                broken = low < lvl_val
                broken_direction = 'Down'
            else:
                broken = False
                broken_direction = None

            # AfterBreakRetouch and BreakSuccess
            after_break_retouch = False
            break_success = False
            if broken:
                if broken_direction == 'Up':
                    # Broken up; retouch if close < level
                    after_break_retouch = close < lvl_val
                    # Success if close >= level (confirmed break)
                    break_success = close >= lvl_val
                else:  # broken_direction == 'Down'
                    # Broken down; retouch if close > level
                    after_break_retouch = close > lvl_val
                    # Success if close <= level (confirmed break)
                    break_success = close <= lvl_val

            stats.append({
                'Date': date,
                'Level': lvl_name,
                'LevelValue': lvl_val,
                'Open': openp,
                'High': high,
                'Low': low,
                'Close': close,
                'FirstTouch': first_touch,
                'Broken': broken,
                'BrokenDirection': broken_direction,
                'AfterBreakRetouch': after_break_retouch if broken else None,
                'BreakSuccess': break_success if broken else None,
            })

    level_df = pd.DataFrame(stats)
    level_df.to_csv(os.path.join(outdir, 'level_game_stats.csv'), index=False)


def aggregate_and_write(df, outdir):
    os.makedirs(outdir, exist_ok=True)

    # Candle state stats
    cs = df[~df['candle_state'].isna()].groupby('candle_state')
    candle_stats = cs.agg(total_count=('candle_state', 'size'),
                          prob_trend_up=('next_day_outcome', lambda s: s.str.contains('Trend_Up_Day').sum() / len(s)),
                          prob_trend_down=('next_day_outcome', lambda s: s.str.contains('Trend_Down_Day').sum() / len(s)),
                          prob_range_chop=('next_day_outcome', lambda s: s.str.contains('Range_Chop_Day').sum() / len(s)),
                          avg_next_day_range_pct=('next_range_pct', 'mean'))
    candle_stats = candle_stats.reset_index()
    candle_stats.to_csv(os.path.join(outdir, 'candle_state_stats.csv'), index=False)

    # Open context stats
    oc = df[~df['open_context'].isna()].groupby('open_context')
    open_stats = oc.agg(total_count=('open_context', 'size'),
                        prob_trend_up=('next_day_outcome', lambda s: s.str.contains('Trend_Up_Day').sum() / len(s)),
                        prob_trend_down=('next_day_outcome', lambda s: s.str.contains('Trend_Down_Day').sum() / len(s)),
                        prob_range_chop=('next_day_outcome', lambda s: s.str.contains('Range_Chop_Day').sum() / len(s)),
                        prob_pdh_break_success=('pdh_break_success', 'sum'),
                        prob_pdl_break_success=('pdl_break_success', 'sum'),
                        prob_false_pdh_break=('false_pdh_break', 'sum'),
                        prob_false_pdl_break=('false_pdl_break', 'sum'),
                        avg_next_day_range_pct=('next_range_pct', 'mean'))
    # convert counts for break flags to probabilities
    open_stats = open_stats.reset_index()
    for col in ['prob_pdh_break_success', 'prob_pdl_break_success', 'prob_false_pdh_break', 'prob_false_pdl_break']:
        open_stats[col] = open_stats[col] / open_stats['total_count']
    open_stats.to_csv(os.path.join(outdir, 'open_context_stats.csv'), index=False)

    # Gap stats with buckets
    df_gap = df[~df['gap_direction'].isna()].copy()
    # bucket: 0-0.5%, 0.5-1%, 1-2%, >2% (percent of previous range)
    pct = df_gap['gap_size_pct'] * 100
    bins = [0, 0.5, 1.0, 2.0, 1e9]
    labels = ['0-0.5%', '0.5-1%', '1-2%', '>2%']
    df_gap['gap_bucket'] = pd.cut(pct.fillna(-1), bins=bins, labels=labels, include_lowest=True)
    # Exclude NaNs (no previous range)
    df_gap = df_gap[~df_gap['gap_bucket'].isna()]

    gg = df_gap.groupby(['gap_direction', 'gap_bucket'])
    gap_stats = gg.agg(total_count=('gap', 'size'),
                       prob_fill_50pct=('fill_50pct', 'mean'),
                       prob_fill_80pct=('fill_80pct', 'mean'),
                       prob_fill_100pct=('fill_100pct', 'mean'),
                       avg_gap_size_pct=('gap_size_pct', 'mean'))
    gap_stats = gap_stats.reset_index()
    gap_stats.to_csv(os.path.join(outdir, 'gap_stats.csv'), index=False)
    
    # write global thresholds (overall percentiles for body_pct_prev)
    try:
        body_series = df['body_pct_prev'].dropna()
        body_70 = float(np.nanpercentile(body_series, 70)) if len(body_series) > 0 else None
        body_30 = float(np.nanpercentile(body_series, 30)) if len(body_series) > 0 else None
        import json
        thresholds = {'body_70': body_70, 'body_30': body_30}
        with open(os.path.join(outdir, 'thresholds.json'), 'w') as f:
            json.dump(thresholds, f)
    except Exception:
        pass


def load_data(input_path: str, header_idx: int = 2) -> pd.DataFrame:
    """Load Excel/CSV using header at zero-based `header_idx`.

    By default `header_idx=2` (i.e. header on Excel row 3, data from row 4).
    """
    if input_path.lower().endswith('.xlsx') or input_path.lower().endswith('.xls'):
        df = pd.read_excel(input_path, header=header_idx)
    else:
        df = pd.read_csv(input_path, header=header_idx)
    # normalize column names
    df.columns = df.columns.astype(str).str.strip()
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', default='/workspaces/Trading-Dashboard/Nifty Data.xlsx', help='Input Excel/CSV file')
    parser.add_argument('--output', '-o', default='data', help='Output directory for CSVs')
    parser.add_argument('--header-row', type=int, default=3, help='1-based row number that contains column headers (default: 3)')
    args = parser.parse_args()

    try:
        header_idx = max(0, args.header_row - 1)
        df = load_data(args.input, header_idx=header_idx)
    except Exception as e:
        print('Failed to read input file:', e)
        sys.exit(1)

    # try to find OHLC columns
    ocol, hcol, lcol, ccol = find_ohlc_cols(df.columns)
    if not all([ocol, hcol, lcol, ccol]):
        print('Could not find Open/High/Low/Close columns automatically. Columns found:', list(df.columns))
        sys.exit(1)

    # normalize column names
    df = df.rename(columns={ocol: 'Open', hcol: 'High', lcol: 'Low', ccol: 'Close'})

    # ensure Date exists and is parsed
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        df = df.sort_values('Date').reset_index(drop=True)
    else:
        df = df.reset_index().rename(columns={'index': 'Date'})

    # previous day metrics
    df['PDH'] = df['High'].shift(1)
    df['PDL'] = df['Low'].shift(1)
    df['PDC'] = df['Close'].shift(1)
    df['PDO'] = df['Open'].shift(1)
    df['prev_close'] = df['PDC']
    df['prev_range'] = df['PDH'] - df['PDL']

    # CPR
    df['PP'] = (df['PDH'] + df['PDL'] + df['PDC']) / 3.0
    df['BC'] = (df['PDH'] + df['PDL']) / 2.0
    df['TC'] = (df['PP'] - df['BC']) + df['PP']
    # Swap if TC < BC to ensure TC is max and BC is min
    swap_mask = df['TC'] < df['BC']
    df.loc[swap_mask, ['TC', 'BC']] = df.loc[swap_mask, ['BC', 'TC']].values
    df['CPR_width'] = df['TC'] - df['BC']

    # candle structure metrics for previous day
    df['range_prev'] = df['prev_range']
    df['body_prev'] = (df['PDC'] - df['PDO']).abs()
    df['upper_wick_prev'] = df['PDH'] - df[['PDO', 'PDC']].max(axis=1)
    df['lower_wick_prev'] = df[['PDO', 'PDC']].min(axis=1) - df['PDL']

    df['body_pct_prev'] = safe_div(df['body_prev'], df['range_prev'])
    df['upper_wick_pct_prev'] = safe_div(df['upper_wick_prev'], df['range_prev'])
    df['lower_wick_pct_prev'] = safe_div(df['lower_wick_prev'], df['range_prev'])
    df['wick_imbalance_prev'] = safe_div(df['upper_wick_prev'] - df['lower_wick_prev'], df['range_prev'])
    df['top_rejection_prev'] = safe_div(df['PDH'] - df['PDC'], df['range_prev'])
    df['bottom_rejection_prev'] = safe_div(df['PDC'] - df['PDL'], df['range_prev'])

    # classify previous candle
    classify_previous_candle(df)

    # classify today's open context relative to previous day
    classify_open_context(df)

    # prepare next-day columns
    df['next_high'] = df['High'].shift(-1)
    df['next_low'] = df['Low'].shift(-1)
    df['next_close'] = df['Close'].shift(-1)
    df['next_open'] = df['Open'].shift(-1)

    # label next day outcomes
    label_next_day_outcomes(df)

    # gap analysis (same-day fill probabilities)
    gap_analysis(df)

    # aggregate and write outputs
    aggregate_and_write(df, args.output)

    # compute and write level game stats
    compute_level_game_stats(df, args.output)

    print('Done. CSVs written to', args.output)


if __name__ == '__main__':
    main()
