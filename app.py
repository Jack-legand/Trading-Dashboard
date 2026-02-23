import json
import os
from datetime import date

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


DATA_DIR = 'data'
SESSION_FILE = os.path.join(DATA_DIR, '.session_cache.json')


def load_session_cache():
    """Load persistent session data from JSON file."""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_session_cache(data):
    """Save session data to JSON file for persistence across reruns."""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f)
    except Exception:
        pass


def load_data():
    candle = pd.read_csv(os.path.join(DATA_DIR, 'candle_state_stats.csv'))
    open_ctx = pd.read_csv(os.path.join(DATA_DIR, 'open_context_stats.csv'))
    gap = pd.read_csv(os.path.join(DATA_DIR, 'gap_stats.csv'))
    th_path = os.path.join(DATA_DIR, 'thresholds.json')
    thresholds = {}
    if os.path.exists(th_path):
        with open(th_path) as f:
            thresholds = json.load(f)

    # try load raw historical OHLC if available for quick checks
    hist = None
    hist_paths = [os.path.join(DATA_DIR, 'historical.csv'), 'Nifty Data.xlsx', 'Nifty Data.csv']
    for p in hist_paths:
        if os.path.exists(p):
            try:
                if p.lower().endswith('.xlsx'):
                    hist = pd.read_excel(p, header=2)
                else:
                    hist = pd.read_csv(p)
                if 'Date' in hist.columns:
                    hist['Date'] = pd.to_datetime(hist['Date'], dayfirst=True, errors='coerce')
                    hist = hist.sort_values('Date').reset_index(drop=True)
                break
            except Exception:
                hist = None

    return candle, open_ctx, gap, thresholds, hist


def compute_cpr(prev_h, prev_l, prev_c):
    pp = (prev_h + prev_l + prev_c) / 3.0
    bc = (prev_h + prev_l) / 2.0
    tc = (pp - bc) + pp
    # Swap if TC < BC to ensure TC is max and BC is min
    if tc < bc:
        tc, bc = bc, tc
    return pp, tc, bc


def classify_candle_from_thresholds(metrics, thresholds):
    b70 = thresholds.get('body_70')
    b30 = thresholds.get('body_30')
    bp = metrics.get('body_pct')
    up = metrics.get('upper_pct')
    lo = metrics.get('lower_pct')
    wick_imb = metrics.get('wick_imb')
    top_rej = metrics.get('top_rej')
    bot_rej = metrics.get('bot_rej')

    if b70 is None or b30 is None or pd.isna(bp):
        base = 'Balanced_Neutral'
    else:
        if (bp > b70) and (up < 0.2) and (lo < 0.2):
            base = 'Strong_Acceptance'
        elif (bp < b30) and ((up > 0.4) or (lo > 0.4)):
            base = 'Exhaustion_Rejection'
        elif (bp > b70) and ((up > 0.3) or (lo > 0.3)):
            base = 'Expansion'
        elif (bp < b30) and (up < 0.3) and (lo < 0.3):
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
    return state


def bucket_gap(pct):
    if pd.isna(pct):
        return None
    p = pct * 100
    if p <= 0.5:
        return '0-0.5%'
    if p <= 1.0:
        return '0.5-1%'
    if p <= 2.0:
        return '1-2%'
    return '>2%'


def welcome_page(candle_df, open_df, gap_df, thresholds, hist_df=None):
    st.title('🎯 NIFTY Edge Dashboard - Welcome')
    st.markdown('---')
    st.markdown('**Enter previous day OHLC and today\'s open to compute edges**')
    
    # Initialize or restore session data
    cache = load_session_cache()
    
    col1, col2 = st.columns(2)
    with col1:
        prev_open = st.number_input('Previous Day Open', 
                                     value=float(cache.get('prev_open', 0.0)), 
                                     format='%.2f',
                                     help='Opening price of the previous trading day')
        prev_high = st.number_input('Previous Day High', 
                                     value=float(cache.get('prev_high', 0.0)), 
                                     format='%.2f',
                                     help='Highest price of the previous trading day')
        prev_low = st.number_input('Previous Day Low', 
                                    value=float(cache.get('prev_low', 0.0)), 
                                    format='%.2f',
                                    help='Lowest price of the previous trading day')
    with col2:
        prev_close = st.number_input('Previous Day Close', 
                                      value=float(cache.get('prev_close', 0.0)), 
                                      format='%.2f',
                                      help='Closing price of the previous trading day')
        today_open = st.number_input("Today's Open", 
                                      value=float(cache.get('today_open', 0.0)), 
                                      format='%.2f',
                                      help='Opening price of today')

    st_date = st.date_input('Date (the day you want to test)', 
                             value=pd.to_datetime(cache.get('test_date', str(date.today()))).date(),
                             help='Select the date to test edge probabilities')

    st.markdown('---')
    
    if st.button('📊 Calculate Edges', use_container_width=True):
        if prev_open == 0 or prev_high == 0 or prev_low == 0 or prev_close == 0:
            st.error('⚠️ Please enter valid OHLC values (not zero)')
            return
        pp, tc, bc = compute_cpr(prev_high, prev_low, prev_close)
        prev_range = prev_high - prev_low
        body = abs(prev_close - prev_open)
        upper = prev_high - max(prev_open, prev_close)
        lower = min(prev_open, prev_close) - prev_low
        body_pct = (body / prev_range) if prev_range != 0 else None
        upper_pct = (upper / prev_range) if prev_range != 0 else None
        lower_pct = (lower / prev_range) if prev_range != 0 else None
        wick_imb = ((upper - lower) / prev_range) if prev_range != 0 else None
        top_rej = ((prev_high - prev_close) / prev_range) if prev_range != 0 else None
        bot_rej = ((prev_close - prev_low) / prev_range) if prev_range != 0 else None

        metrics = dict(body_pct=body_pct, upper_pct=upper_pct, lower_pct=lower_pct,
                       wick_imb=wick_imb, top_rej=top_rej, bot_rej=bot_rej)
        candle_state = classify_candle_from_thresholds(metrics, thresholds)

        # open context
        if today_open > prev_high:
            pos = 'Open_Above_PDH'
        elif today_open < prev_low:
            pos = 'Open_Below_PDL'
        else:
            pos = 'Open_Inside_Prev_Range'

        if today_open > tc:
            cpr_pos = 'Above_CPR'
        elif today_open < bc:
            cpr_pos = 'Below_CPR'
        else:
            cpr_pos = 'Inside_CPR'

        # Quartile classification: only applies when open is INSIDE previous range
        if pos == 'Open_Inside_Prev_Range':
            if prev_range == 0:
                quart = 'Open_Middle_Half'
            else:
                if (prev_high - today_open) / prev_range < 0.25:
                    quart = 'Open_Top_Quartile'
                elif (today_open - prev_low) / prev_range < 0.25:
                    quart = 'Open_Bottom_Quartile'
                else:
                    quart = 'Open_Middle_Half'
            open_context = f"{pos}|{cpr_pos}|{quart}"
        else:
            open_context = f"{pos}|{cpr_pos}" 

        gap = today_open - prev_close
        gap_dir = 'Gap_Up' if gap > 0 else ('Gap_Down' if gap < 0 else 'No_Gap')
        gap_pct = abs(gap) / prev_close if prev_close != 0 else None
        gap_bucket = bucket_gap(gap_pct)

        edge_result = dict(
            prev_open=prev_open, prev_high=prev_high, prev_low=prev_low, prev_close=prev_close,
            today_open=today_open, PP=pp, TC=tc, BC=bc, prev_range=prev_range,
            body=body, upper=upper, lower=lower, body_pct=body_pct, upper_pct=upper_pct, lower_pct=lower_pct,
            wick_imb=wick_imb, top_rej=top_rej, bot_rej=bot_rej,
            candle_state=candle_state, open_context=open_context, gap_dir=gap_dir, gap_pct=gap_pct, gap_bucket=gap_bucket,
            test_date=str(st_date)
        )
        
        # Save to persistent session
        cache.update(edge_result)
        save_session_cache(cache)
        st.session_state['edge_result'] = edge_result
        st.session_state['nav_page'] = 'Edge Detection'
        
        # Display verification section with all key metrics
        st.success('✅ Edges computed successfully!')
        
        st.markdown('### 📍 Previous Day Summary')
        col1, col2, col3, col4 = st.columns(4)
        col1.metric('High', f'{prev_high:.2f}')
        col2.metric('Low', f'{prev_low:.2f}')
        col3.metric('Close', f'{prev_close:.2f}')
        col4.metric('Range', f'{prev_range:.2f}')
        
        st.markdown('### 📊 CPR Levels (Central Pivot Range)')
        col1, col2, col3 = st.columns(3)
        col1.metric('Pivot Point (PP)', f'{pp:.2f}', help='Central support/resistance level')
        col2.metric('Top CPR (TC)', f'{tc:.2f}', help='Highest resistance level')
        col3.metric('Bottom CPR (BC)', f'{bc:.2f}', help='Lowest support level')
        
        st.markdown('### 📈 Today\'s Gap Analysis')
        col1, col2, col3, col4 = st.columns(4)
        col1.metric('Today\'s Open', f'{today_open:.2f}')
        col2.metric('Gap Size', f'{abs(gap):.2f}', delta=gap_dir)
        col3.metric('Gap %', f'{abs(gap_pct)*100:.2f}%' if gap_pct else 'N/A', help='Gap as percentage of previous close')
        col4.metric('Gap Bucket', gap_bucket if gap_bucket else 'Unknown', help='Gap size classification')
        
        st.markdown('### 🎯 Open Context Classification')
        col1, col2, col3 = st.columns(3)
        col1.metric('Position', pos, help='Open relative to previous day range')
        col2.metric('CPR Position', cpr_pos, help='Open relative to CPR levels')
        col3.metric('Quartile', quart if pos == 'Open_Inside_Prev_Range' else '—', help='Position within previous range')

        # show historical actual next-day outcome if historical loaded
        if hist_df is not None:
            try:
                sd = pd.to_datetime(st_date)
                match = hist_df[hist_df['Date'] == sd]
                if not match.empty:
                    idx = match.index[0]
                    if idx + 1 < len(hist_df):
                        today_row = hist_df.loc[idx]
                        next_row = hist_df.loc[idx + 1]
                        nh = next_row.get('High')
                        nl = next_row.get('Low')
                        nc = next_row.get('Close')
                        no = next_row.get('Open')
                        nrange = nh - nl if pd.notna(nh) and pd.notna(nl) else None
                        if nrange and nrange != 0:
                            nbody_pct = abs(nc - no) / nrange
                        else:
                            nbody_pct = None
                        actual_parts = []
                        if nbody_pct is not None and nbody_pct > 0.6 and (nc > no):
                            actual_parts.append('Trend_Up_Day')
                        elif nbody_pct is not None and nbody_pct > 0.6 and (nc < no):
                            actual_parts.append('Trend_Down_Day')
                        else:
                            actual_parts.append('Range_Chop_Day')

                        pdh = today_row.get('High')
                        pdl = today_row.get('Low')
                        if (nh > pdh) and (nc < pdh):
                            actual_parts.append('False_PDH_Break')
                        if (nl < pdl) and (nc > pdl):
                            actual_parts.append('False_PDL_Break')
                        if (nh > pdh) and (nc >= pdh):
                            actual_parts.append('PDH_Break_Success')
                        if (nl < pdl) and (nc <= pdl):
                            actual_parts.append('PDL_Break_Success')

                        st.info('📈 **Historical check:** actual next-day outcome for selected Date: **' + ','.join(actual_parts) + '**')
                    else:
                        st.info('Historical loaded but next-day data not available for selected date.')
                else:
                    st.info('Selected date not present in loaded historical data.')
            except Exception:
                st.info('Could not compute historical check.')

    st.info('Use the sidebar 👈 to navigate to **Edge Detection** page')


def edge_detection_page(candle_df, open_df, gap_df, thresholds):
    st.title('🔍 Edge Detection')
    if 'edge_result' not in st.session_state or not st.session_state['edge_result']:
        # Try load from cache
        cache = load_session_cache()
        if cache and 'candle_state' in cache:
            st.session_state['edge_result'] = cache
        else:
            st.warning('❌ No edge computed yet. Go to **Welcome** and calculate edges first.')
            return

    er = st.session_state['edge_result']
    st.markdown('---')
    
    # Candle Structure Game - Styled Container
    with st.container():
        st.markdown('### 🕯️ Candle Structure Game')
        st.markdown(f"**Classified Candle State:** `{er['candle_state']}`")
        row = candle_df[candle_df['candle_state'] == er['candle_state']]
        if not row.empty:
            r = row.iloc[0]
            st.metric('Sample Size', int(r['total_count']), help='Number of historical occurrences of this candle state')
            
            fig = make_subplots(rows=1, cols=3, specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}]])
            bullish = float(r['prob_trend_up']) * 100
            bearish = float(r['prob_trend_down']) * 100
            sideways = float(r['prob_range_chop']) * 100
            
            fig.add_trace(go.Indicator(
                mode='gauge+number+delta', value=bullish,
                title={'text': 'Bullish %'},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': '#2ecc71'}, 'threshold': {'line': {'color': 'gray'}, 'thickness': 0.1, 'value': 50}},
                domain={'x': [0, 0.32]}
            ), row=1, col=1)
            
            fig.add_trace(go.Indicator(
                mode='gauge+number+delta', value=bearish,
                title={'text': 'Bearish %'},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': '#e74c3c'}, 'threshold': {'line': {'color': 'gray'}, 'thickness': 0.1, 'value': 50}},
                domain={'x': [0.34, 0.66]}
            ), row=1, col=2)
            
            fig.add_trace(go.Indicator(
                mode='gauge+number+delta', value=sideways,
                title={'text': 'Sideways %'},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': '#f39c12'}, 'threshold': {'line': {'color': 'gray'}, 'thickness': 0.1, 'value': 50}},
                domain={'x': [0.68, 1.0]}
            ), row=1, col=3)
            
            fig.update_layout(height=280, margin={'t': 30, 'b': 0})
            st.plotly_chart(fig, use_container_width=True)
            
            st.metric('Avg Next Day Range %', f"{float(r['avg_next_day_range_pct']):.2f}", 
                     help='Average percentage range expansion on the next day')
        else:
            st.warning('⚠️ No matching candle state in historical stats.')
    
    st.markdown('---')

    # Level Game - Styled Container
    with st.container():
        st.markdown('### 📊 Level Game')
        st.markdown(f"**Open Context:** `{er['open_context']}`")
        
        row = open_df[open_df['open_context'] == er['open_context']]
        if not row.empty:
            r = row.iloc[0]
            st.metric('Sample Size', int(r['total_count']), help='Number of historical occurrences of this open context')
            
            # Display trend probabilities with gauges
            fig2 = make_subplots(rows=1, cols=2, specs=[[{'type': 'indicator'}, {'type': 'indicator'}]])
            trend_up = float(r['prob_trend_up']) * 100
            trend_down = float(r['prob_trend_down']) * 100
            
            fig2.add_trace(go.Indicator(
                mode='gauge+number', value=trend_up,
                title={'text': 'Trend Up %'},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': '#3498db'}},
                domain={'x': [0, 0.48]}
            ), row=1, col=1)
            
            fig2.add_trace(go.Indicator(
                mode='gauge+number', value=trend_down,
                title={'text': 'Trend Down %'},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': '#c0392b'}},
                domain={'x': [0.52, 1.0]}
            ), row=1, col=2)
            
            fig2.update_layout(height=220, margin={'t': 30, 'b': 0})
            st.plotly_chart(fig2, use_container_width=True)
            
            # Display all breakdown probabilities in a grid with exact numerical values
            st.markdown('**Key Probability Breakdowns:**')
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric('Range/Chop Day', 
                       f"{float(r.get('prob_range_chop', 0)):.2%}",
                       help='Probability of range-bound / choppy day')
            col2.metric('False PDH Break', 
                       f"{float(r.get('prob_false_pdh_break', 0)):.2%}",
                       help='Probability of false breakout above PDH')
            col3.metric('False PDL Break', 
                       f"{float(r.get('prob_false_pdl_break', 0)):.2%}",
                       help='Probability of false breakout below PDL')
            col4.metric('Sample Count', 
                       f"{int(r['total_count'])}", 
                       help='Trades matching this context')
            
            col5, col6, col7, col8 = st.columns(4)
            col5.metric('PDH Break Success', 
                       f"{float(r['prob_pdh_break_success']):.2%}", 
                       help='Probability of successful breakout above PDH')
            col6.metric('PDL Break Success', 
                       f"{float(r['prob_pdl_break_success']):.2%}",
                       help='Probability of successful breakout below PDL')
            col7.metric('Trend Up %', f"{trend_up:.1f}%", help='Bullish probability')
            col8.metric('Trend Down %', f"{trend_down:.1f}%", help='Bearish probability')
        else:
            st.warning('⚠️ No matching open context in historical stats.')
    
    st.markdown('---')

    # Gap Game - Styled Container
    with st.container():
        st.markdown('### 📉 Gap Game')
        st.markdown(f"**Gap Direction:** `{er['gap_dir']}` | **Gap Bucket:** `{er['gap_bucket']}`")
        
        if er['gap_bucket'] is not None:
            row = gap_df[(gap_df['gap_direction'] == er['gap_dir']) & (gap_df['gap_bucket'] == er['gap_bucket'])]
            if not row.empty:
                r = row.iloc[0]
                vals = [float(r['prob_fill_50pct']), float(r['prob_fill_80pct']), float(r['prob_fill_100pct'])]
                labels = ['50% Fill', '80% Fill', '100% Fill']
                colors = ['#95a5a6', '#f39c12', '#27ae60']
                
                fig3 = go.Figure(go.Bar(
                    x=labels, 
                    y=[v * 100 for v in vals],
                    marker=dict(color=colors, line=dict(color='#2c3e50', width=2)),
                    text=[f'{v*100:.1f}%' for v in vals],
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Probability: %{y:.1f}%<extra></extra>'
                ))
                
                fig3.update_layout(yaxis_title='Probability (%)', height=320, 
                                 plot_bgcolor='rgba(240,240,240,0.5)',
                                 xaxis_title='Fill Levels')
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.warning('⚠️ No exact gap bucket; try nearest bucket in data.')
        else:
            st.info('ℹ️ Insufficient data to classify gap bucket.')
    
    st.markdown('---')
    
    # Summary Card - Combine all three games into actionable signal
    with st.container():
        st.markdown('### 🎯 Overall Trading Signal Summary')
        
        # Retrieve computed probability scores for synthesis
        try:
            # Candle Game probabilities
            candle_row = candle_df[candle_df['candle_state'] == er['candle_state']]
            candle_bull = float(candle_row.iloc[0]['prob_trend_up']) if not candle_row.empty else 0
            candle_bear = float(candle_row.iloc[0]['prob_trend_down']) if not candle_row.empty else 0
            
            # Level Game probabilities
            level_row = open_df[open_df['open_context'] == er['open_context']]
            level_bull = float(level_row.iloc[0]['prob_trend_up']) if not level_row.empty else 0
            level_bear = float(level_row.iloc[0]['prob_trend_down']) if not level_row.empty else 0
            
            # Gap Game probabilities - determine most likely outcome
            gap_row = gap_df[(gap_df['gap_direction'] == er['gap_dir']) & (gap_df['gap_bucket'] == er['gap_bucket'])]
            gap_fill_prob = float(gap_row.iloc[0]['prob_fill_100pct']) if not gap_row.empty else 0
            
            # Compute weighted consensus (simple average)
            consensus_bull = (candle_bull + level_bull) / 2.0
            consensus_bear = (candle_bear + level_bear) / 2.0
            
            # Determine directional bias
            if consensus_bull > consensus_bear + 0.05:
                bias = '📈 BULLISH BIAS'
                bias_color = '🟢'
            elif consensus_bear > consensus_bull + 0.05:
                bias = '📉 BEARISH BIAS'
                bias_color = '🔴'
            else:
                bias = '➡️ NEUTRAL / SIDEWAYS'
                bias_color = '🟡'
            
            # Determine gap fill likelihood
            gap_signal = ''
            if er['gap_dir'] == 'Gap_Up' and gap_fill_prob > 0.5:
                gap_signal = ' → Gap may fill lower (watch support)'
            elif er['gap_dir'] == 'Gap_Down' and gap_fill_prob > 0.5:
                gap_signal = ' → Gap may fill higher (watch resistance)'
            
            # Display summary in highlighted container
            col_signal, col_confidence = st.columns([2, 1])
            with col_signal:
                st.markdown(f"**{bias_color} {bias}{gap_signal}**")
                st.markdown(f"Candle Game: {candle_bull:.1%} Up / {candle_bear:.1%} Down  \n"
                           f"Level Game: {level_bull:.1%} Up / {level_bear:.1%} Down  \n"
                           f"Gap Fill Probability: {gap_fill_prob:.1%}")
            with col_confidence:
                avg_confidence = (abs(consensus_bull - consensus_bear) * 100)
                st.metric('Confidence', f'{avg_confidence:.0f}%', help='Edge conviction level (0-100)')
            
            # Action recommendations
            st.markdown('**📋 Action Guide:**')
            if consensus_bull > 0.55:
                st.info('✅ Consider **long entries** with PDH breakout confirmation')
            elif consensus_bear > 0.55:
                st.info('✅ Consider **short entries** with PDL breakdown confirmation')
            else:
                st.info('⚠️ Weak signal → wait for **intraday confirmation** before trade')
                
        except Exception as e:
            st.warning(f'⚠️ Could not compute summary signal (data incomplete). Trade manually with caution.')
    
    st.markdown('---')
    if st.button('🔄 Clear Data & Start Over', use_container_width=True):
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        st.session_state.clear()
        st.session_state['nav_page'] = 'Welcome'
        st.success('Data cleared. Use the sidebar to go back to Welcome.')


def trade_logging_page():
    st.title('📝 Log Your Trade')
    st.markdown('---')
    st.write('Use this form to record trades; entries append to `data/trade_log.csv`')
    form = st.form('trade_form')
    edge_type = form.selectbox('Edge Type', ['Structural Game', 'Level Game', 'Gap Game'],
                               help='Which edge type triggered this trade')
    market_direction = form.selectbox('Market Direction', ['Going Up', 'Falling Down', 'Sideways'],
                                     help='Expected market direction')
    harmony = form.radio('Harmony with Capital', ['Yes', 'No'],
                        help='Does this trade align with your risk management rules?')
    entry_price = form.number_input('Entry Price', value=0.0, format='%.2f')
    stop_loss = form.number_input('Stop Loss', value=0.0, format='%.2f')
    num_lots = form.number_input('Number of Lots', value=1, step=1)
    qty_per_lot = form.number_input('Qty per Lot', value=65, step=1)
    instrument = form.selectbox('Instrument', ['Call Option', 'Put Option'])
    pre_trade = form.radio('Data entered before trade?', ['Yes', 'No'],
                          help='Critical for discipline tracking')
    exit_price = form.number_input('Exit Price (optional)', value=0.0, format='%.2f')
    charges = form.number_input('Total Charges (optional)', value=0.0, format='%.2f')
    exit_reason = form.selectbox('Exit Reason', ['SL hit', 'Target hit', 'Manual exit', 'Time exit'])
    trade_date = form.date_input('Trade Date', value=date.today())

    submitted = form.form_submit_button('💾 Save Trade', use_container_width=True)
    if submitted:
        risk_per_lot = abs(entry_price - stop_loss) * qty_per_lot
        total_risk = risk_per_lot * num_lots
        record = dict(timestamp=pd.Timestamp.now(), edge_type=edge_type, market_direction=market_direction,
                      harmony=harmony, entry_price=entry_price, stop_loss=stop_loss, num_lots=num_lots,
                      qty_per_lot=qty_per_lot, instrument=instrument, pre_trade_data_flag=pre_trade,
                      exit_price=exit_price if exit_price != 0.0 else None, charges=charges if charges != 0.0 else None,
                      exit_reason=exit_reason, trade_date=str(trade_date), risk_amount=total_risk)
        os.makedirs(DATA_DIR, exist_ok=True)
        log_path = os.path.join(DATA_DIR, 'trade_log.csv')
        df_new = pd.DataFrame([record])
        if os.path.exists(log_path):
            df_new.to_csv(log_path, mode='a', header=False, index=False)
        else:
            df_new.to_csv(log_path, index=False)
        st.success('✅ Trade saved successfully!')


def insight_page():
    st.title('📊 Trade Insights & Discipline Monitor')
    st.markdown('---')
    log_path = os.path.join(DATA_DIR, 'trade_log.csv')
    if not os.path.exists(log_path):
        st.info('ℹ️ No trades logged yet.')
        return
    df = pd.read_csv(log_path)
    closed = df[~df['exit_price'].isna()].copy()
    if closed.empty:
        st.info('ℹ️ No closed trades to analyze yet.')
        return

    def pnl_row(r):
        if r['instrument'] == 'Call Option':
            return (r['exit_price'] - r['entry_price']) * r['qty_per_lot'] * r['num_lots'] - (r.get('charges') or 0)
        else:
            return (r['entry_price'] - r['exit_price']) * r['qty_per_lot'] * r['num_lots'] - (r.get('charges') or 0)

    closed['pnl'] = closed.apply(pnl_row, axis=1)
    total_pnl = closed['pnl'].sum()
    gross_profit = closed[closed['pnl'] > 0]['pnl'].sum()
    gross_loss = -closed[closed['pnl'] < 0]['pnl'].sum()
    profit_factor = (gross_profit / gross_loss) if gross_loss != 0 else None
    win_rate = len(closed[closed['pnl'] > 0]) / len(closed)
    avg_risk = df['risk_amount'].astype(float).mean()
    discipline = len(df[df['pre_trade_data_flag'] == 'Yes']) / len(df)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric('Total P&L', f"₹{total_pnl:.2f}", help='Cumulative profit/loss')
    col2.metric('Win Rate', f"{win_rate:.2%}", help='Percentage of winning trades')
    col3.metric('Avg Risk', f"₹{avg_risk:.2f}", help='Average risk per trade')
    col4.metric('Profit Factor', f"{profit_factor:.2f}" if profit_factor else 'N/A', help='Gross Profit / Gross Loss')
    col5.metric('Discipline 🎯', f"{discipline:.2%}", help='% of trades with pre-planned data')

    st.markdown('---')
    
    st.subheader('📈 Equity Curve')
    closed_sorted = closed.sort_values('timestamp')
    closed_sorted['cum_pnl'] = closed_sorted['pnl'].cumsum()
    
    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(x=closed_sorted['timestamp'], y=closed_sorted['cum_pnl'],
                                    fill='tozeroy', mode='lines+markers', name='Cumulative P&L',
                                    line=dict(color='#3498db', width=2), marker=dict(size=6)))
    fig_equity.update_layout(yaxis_title='Cumulative P&L (₹)', xaxis_title='Date', height=350)
    st.plotly_chart(fig_equity, use_container_width=True)

    st.subheader('📊 Risk Pattern')
    fig_risk = go.Figure()
    fig_risk.add_trace(go.Bar(x=closed_sorted['timestamp'], y=closed_sorted['risk_amount'],
                             marker=dict(color='#e74c3c', line=dict(color='#c0392b', width=1)),
                             text=closed_sorted['risk_amount'].round(0),
                             textposition='outside',
                             hovertemplate='<b>%{x}</b><br>Risk: ₹%{y:.2f}<extra></extra>'))
    fig_risk.update_layout(yaxis_title='Risk Amount (₹)', xaxis_title='Date', height=350)
    st.plotly_chart(fig_risk, use_container_width=True)

    st.subheader('📋 Execution Discipline')
    discipline_df = closed[['timestamp', 'pre_trade_data_flag', 'exit_reason', 'pnl']].sort_values('timestamp', ascending=False).copy()
    discipline_df.columns = ['Timestamp', 'Data Pre-Planned', 'Exit Reason', 'P&L']
    st.dataframe(discipline_df, use_container_width=True, height=400)


def main():
    st.set_page_config(page_title='NIFTY Edge Dashboard v2.1', layout='wide', initial_sidebar_state='expanded')
    
    st.sidebar.title('🚀 Navigation')
    st.sidebar.markdown('**Version 2.1** | Production Ready')
    st.sidebar.markdown('---')
    pages = ['Welcome', 'Edge Detection', 'Trade Logging', 'Insight']
    default_page = st.session_state.get('nav_page', 'Welcome')
    try:
        default_index = pages.index(default_page)
    except ValueError:
        default_index = 0
    page = st.sidebar.radio('Go to', pages, index=default_index)

    candle_df, open_df, gap_df, thresholds, hist_df = load_data()

    if page == 'Welcome':
        welcome_page(candle_df, open_df, gap_df, thresholds, hist_df)
    elif page == 'Edge Detection':
        edge_detection_page(candle_df, open_df, gap_df, thresholds)
    elif page == 'Trade Logging':
        trade_logging_page()
    elif page == 'Insight':
        insight_page()


if __name__ == '__main__':
    main()
