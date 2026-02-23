#!/usr/bin/env python3
import os
import sys

# Change to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add current directory to path
sys.path.insert(0, '.')

# Import and run the backtest main function
if __name__ == '__main__':
    import pandas as pd
    import numpy as np
    from backtest_nifty import (
        load_data, find_ohlc_cols, classify_previous_candle, 
        classify_open_context, label_next_day_outcomes, gap_analysis,
        aggregate_and_write, safe_div
    )
    
    # Load data  
    input_path = 'Nifty Data.xlsx'
    output_dir = 'data'
    header_idx = 2  # 0-based for header_row=3
    
    print(f"Loading data from {input_path}...")
    if input_path.lower().endswith('.xlsx'):
        df = pd.read_excel(input_path, header=header_idx)
    else:
        df = pd.read_csv(input_path, header=header_idx)
    
    df.columns = df.columns.astype(str).str.strip()
    
    # Find OHLC columns
    ocol, hcol, lcol, ccol = find_ohlc_cols(df.columns)
    if not all([ocol, hcol, lcol, ccol]):
        print('Could not find Open/High/Low/Close columns automatically.')
        print(f'Columns found: {list(df.columns)}')
        sys.exit(1)
    
    # Normalize column names
    df = df.rename(columns={ocol: 'Open', hcol: 'High', lcol: 'Low', ccol: 'Close'})
    
    # Parse dates
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        df = df.sort_values('Date').reset_index(drop=True)
    else:
        df = df.reset_index().rename(columns={'index': 'Date'})
    
    print(f"Loaded {len(df)} rows of data")
    
    # Previous day metrics
    df['PDH'] = df['High'].shift(1)
    df['PDL'] = df['Low'].shift(1)
    df['PDC'] = df['Close'].shift(1)
    df['PDO'] = df['Open'].shift(1)
    df['prev_close'] = df['PDC']
    df['prev_range'] = df['PDH'] - df['PDL']
    
    # CPR with corrected formulas
    print("Computing CPR with corrected formulas...")
    df['PP'] = (df['PDH'] + df['PDL'] + df['PDC']) / 3.0
    df['BC'] = (df['PDH'] + df['PDL']) / 2.0
    df['TC'] = (df['PP'] - df['BC']) + df['PP']
    # Swap if TC < BC to ensure TC is max and BC is min
    swap_mask = df['TC'] < df['BC']
    df.loc[swap_mask, ['TC', 'BC']] = df.loc[swap_mask, ['BC', 'TC']].values
    df['CPR_width'] = df['TC'] - df['BC']
    
    # Candle structure metrics for previous day
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
    
    # Classify previous candle
    print("Classifying previous candles...")
    classify_previous_candle(df)
    
    # Classify open context
    print("Classifying open context...")
    classify_open_context(df)
    
    # Prepare next-day columns
    df['next_high'] = df['High'].shift(-1)
    df['next_low'] = df['Low'].shift(-1)
    df['next_close'] = df['Close'].shift(-1)
    df['next_open'] = df['Open'].shift(-1)
    
    # Label next day outcomes
    print("Labeling next day outcomes...")
    label_next_day_outcomes(df)
    
    # Gap analysis
    print("Analyzing gaps...")
    gap_analysis(df)
    
    # Aggregate and write
    print("Writing CSV files...")
    aggregate_and_write(df, output_dir)
    
    print(f'\n✅ Done! CSVs written to {output_dir}')
    print('Files generated:')
    print('  - candle_state_stats.csv')
    print('  - open_context_stats.csv')
    print('  - gap_stats.csv')
    print('  - thresholds.json')
