import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time as time_module
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="F&O Stock Screener - Intraday",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .bullish { color: #00C853; font-weight: bold; }
    .bearish { color: #FF1744; font-weight: bold; }
    .metric-card {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .header-style {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("📊 F&O Stock Screener - Top 10 Bullish & Bearish")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Screener Settings")
    
    # Time filter
    current_time = datetime.now().time()
    st.info(f"🕐 Current Time: {current_time.strftime('%H:%M:%S')} IST")
    
    # Auto-refresh
    auto_refresh = st.checkbox("🔄 Auto-refresh (60s)", value=True)
    if auto_refresh:
        st.write("Refreshing every 60 seconds...")
        time_module.sleep(60)
        st.rerun()
    
    # Manual refresh
    if st.button("🔄 Manual Refresh", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    
    # Indicator settings
    st.subheader("📊 Indicator Parameters")
    rsi_period = st.slider("RSI Period", 7, 21, 14)
    macd_fast = st.slider("MACD Fast", 8, 15, 12)
    macd_slow = st.slider("MACD Slow", 20, 30, 26)
    macd_signal = st.slider("MACD Signal", 5, 12, 9)
    ema_period = st.slider("EMA Period", 10, 50, 20)
    volume_ma = st.slider("Volume MA Period", 10, 30, 20)
    
    st.markdown("---")
    st.caption("Data Source: Yahoo Finance")
    st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# F&O Stock List (NSE F&O stocks)
@st.cache_data(ttl=60)
def get_fno_stocks():
    """List of major F&O stocks"""
    fno_stocks = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS",
        "LT.NS", "BAJFINANCE.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS",
        "TITAN.NS", "ASIANPAINT.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS",
        "ULTRACEMCO.NS", "NTPC.NS", "POWERGRID.NS", "M&M.NS", "TATAMOTORS.NS",
        "TATASTEEL.NS", "JSWSTEEL.NS", "GRASIM.NS", "ADANIPORTS.NS", "ADANIENT.NS",
        "BAJAJFINSV.NS", "BAJAJ-AUTO.NS", "NESTLEIND.NS", "DRREDDY.NS", "CIPLA.NS",
        "BPCL.NS", "ONGC.NS", "COALINDIA.NS", "HDFCLIFE.NS", "SBILIFE.NS",
        "DIVISLAB.NS", "APOLLOHOSP.NS", "EICHERMOT.NS", "HDFC.NS", "BRITANNIA.NS",
        "HEROMOTOCO.NS", "SHREECEM.NS", "HINDALCO.NS", "UPL.NS", "INDUSINDBK.NS"
    ]
    return fno_stocks

# Technical Indicators Calculation
def calculate_rsi(data, period=14):
    """Calculate RSI"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = data['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def calculate_adx(data, period=14):
    """Calculate ADX"""
    high = data['High']
    low = data['Low']
    close = data['Close']
    
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    
    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    plus_di = 100 * (plus_dm.ewm(alpha=1/period).mean() / atr)
    minus_di = abs(100 * (minus_dm.ewm(alpha=1/period).mean() / atr))
    dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
    adx = dx.rolling(period).mean()
    
    return adx.iloc[-1], plus_di.iloc[-1], minus_di.iloc[-1]

@st.cache_data(ttl=60)
def fetch_stock_data(symbol):
    """Fetch stock data from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period='5d', interval='5m')
        if df.empty:
            return None, None
        
        # Current data
        current_price = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change = ((current_price - prev_close) / prev_close) * 100
        
        # Volume analysis
        avg_volume = df['Volume'].rolling(20).mean().iloc[-1]
        current_volume = df['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # RSI
        rsi = calculate_rsi(df).iloc[-1]
        
        # MACD
        macd, signal, hist = calculate_macd(df)
        
        # EMA
        ema = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        
        # ADX
        adx, plus_di, minus_di = calculate_adx(df)
        
        # Price position vs EMA
        price_vs_ema = ((current_price - ema) / ema) * 100
        
        info = stock.info
        stock_name = info.get('longName', symbol.replace('.NS', ''))
        sector = info.get('sector', 'N/A')
        
        return {
            'symbol': symbol.replace('.NS', ''),
            'name': stock_name,
            'sector': sector,
            'price': current_price,
            'change_percent': change,
            'volume': current_volume,
            'avg_volume': avg_volume,
            'volume_ratio': volume_ratio,
            'rsi': rsi,
            'macd': macd.iloc[-1],
            'macd_signal': signal.iloc[-1],
            'macd_histogram': hist.iloc[-1],
            'price_vs_ema': price_vs_ema,
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di,
        }, df
    except Exception as e:
        return None, None

def calculate_bullish_score(data):
    """Calculate bullish score based on multiple indicators"""
    score = 0
    
    # RSI check (40-70 range for bullish)
    if 40 <= data['rsi'] <= 70:
        score += 1
    if data['rsi'] > 50:
        score += 1
    
    # MACD check
    if data['macd'] > data['macd_signal']:
        score += 2
    if data['macd_histogram'] > 0:
        score += 1
    
    # Price vs EMA
    if data['price_vs_ema'] > 0:
        score += 1
    
    # Volume check
    if data['volume_ratio'] > 1.2:
        score += 1
    
    # ADX check (strong trend)
    if data['adx'] > 25 and data['plus_di'] > data['minus_di']:
        score += 2
    
    # Price change positive
    if data['change_percent'] > 0:
        score += 1
    
    return score

def calculate_bearish_score(data):
    """Calculate bearish score based on multiple indicators"""
    score = 0
    
    # RSI check
    if data['rsi'] < 50:
        score += 1
    if data['rsi'] < 40:
        score += 1
    
    # MACD check
    if data['macd'] < data['macd_signal']:
        score += 2
    if data['macd_histogram'] < 0:
        score += 1
    
    # Price vs EMA
    if data['price_vs_ema'] < 0:
        score += 1
    
    # Volume check
    if data['volume_ratio'] > 1.2:
        score += 1
    
    # ADX check (strong trend)
    if data['adx'] > 25 and data['minus_di'] > data['plus_di']:
        score += 2
    
    # Price change negative
    if data['change_percent'] < 0:
        score += 1
    
    return score

# Main processing
with st.spinner('Fetching live data from Yahoo Finance...'):
    fno_list = get_fno_stocks()
    stock_data_list = []
    
    progress_bar = st.progress(0)
    for idx, symbol in enumerate(fno_list):
        data, _ = fetch_stock_data(symbol)
        if data:
            # Calculate scores
            data['bullish_score'] = calculate_bullish_score(data)
            data['bearish_score'] = calculate_bearish_score(data)
            stock_data_list.append(data)
        
        progress_bar.progress((idx + 1) / len(fno_list))
    
    progress_bar.empty()

if stock_data_list:
    df_all = pd.DataFrame(stock_data_list)
    
    # Sort for bullish and bearish
    df_bullish = df_all.nlargest(15, 'bullish_score').head(10)
    df_bearish = df_all.nlargest(15, 'bearish_score').head(10)
    
    # Display Dashboard
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🟢 Top 10 Bullish Stocks")
        st.markdown("---")
        
        for idx, row in df_bullish.iterrows():
            with st.container():
                col_metric, col_chart = st.columns([3, 1])
                
                with col_metric:
                    st.markdown(f"""
                        <div class="metric-card">
                            <h4 style="margin:0">{row['name']} ({row['symbol']})</h4>
                            <span class="bullish">₹{row['price']:.2f}</span> 
                            <span class="bullish">({row['change_percent']:.2f}%)</span>
                            <br>
                            <small>
                            RSI: {row['rsi']:.1f} | 
                            Volume Ratio: {row['volume_ratio']:.2f}x | 
                            Score: {row['bullish_score']:.0f}/10
                            </small>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_chart:
                    # Mini bar chart for indicators
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = row['rsi'],
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        gauge = {
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "green" if row['rsi'] > 50 else "red"},
                            'threshold': {
                                'line': {'color': "black", 'width': 2},
                                'thickness': 0.75,
                                'value': 50
                            }
                        },
                        title = {'text': "RSI"}
                    ))
                    fig.update_layout(height=120, margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
    
    with col2:
        st.markdown("### 🔴 Top 10 Bearish Stocks")
        st.markdown("---")
        
        for idx, row in df_bearish.iterrows():
            with st.container():
                col_metric, col_chart = st.columns([3, 1])
                
                with col_metric:
                    st.markdown(f"""
                        <div class="metric-card">
                            <h4 style="margin:0">{row['name']} ({row['symbol']})</h4>
                            <span class="bearish">₹{row['price']:.2f}</span> 
                            <span class="bearish">({row['change_percent']:.2f}%)</span>
                            <br>
                            <small>
                            RSI: {row['rsi']:.1f} | 
                            Volume Ratio: {row['volume_ratio']:.2f}x | 
                            Score: {row['bearish_score']:.0f}/10
                            </small>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_chart:
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = row['rsi'],
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        gauge = {
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "red" if row['rsi'] < 50 else "green"},
                            'threshold': {
                                'line': {'color': "black", 'width': 2},
                                'thickness': 0.75,
                                'value': 50
                            }
                        },
                        title = {'text': "RSI"}
                    ))
                    fig.update_layout(height=120, margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
    
    # Summary Statistics
    st.markdown("---")
    st.markdown("### 📊 Market Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        bullish_count = len(df_all[df_all['change_percent'] > 0])
        st.metric("Stocks Up", f"{bullish_count}/{len(df_all)}", 
                 f"{(bullish_count/len(df_all)*100):.1f}%")
    
    with col2:
        bearish_count = len(df_all[df_all['change_percent'] < 0])
        st.metric("Stocks Down", f"{bearish_count}/{len(df_all)}", 
                 f"{(bearish_count/len(df_all)*100):.1f}%")
    
    with col3:
        avg_rsi = df_all['rsi'].mean()
        st.metric("Average RSI", f"{avg_rsi:.1f}", 
                 "Overbought" if avg_rsi > 60 else "Oversold" if avg_rsi < 40 else "Neutral")
    
    with col4:
        avg_volume = df_all['volume_ratio'].mean()
        st.metric("Avg Volume Ratio", f"{avg_volume:.2f}x",
                 "High" if avg_volume > 1.5 else "Normal")
    
    # Download button
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        csv_bullish = df_bullish.to_csv(index=False)
        st.download_button(
            label="📥 Download Bullish Stocks CSV",
            data=csv_bullish,
            file_name=f"bullish_stocks_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    with col2:
        csv_bearish = df_bearish.to_csv(index=False)
        st.download_button(
            label="📥 Download Bearish Stocks CSV",
            data=csv_bearish,
            file_name=f"bearish_stocks_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    # Raw Data
    with st.expander("🔍 View All Stock Data"):
        st.dataframe(df_all, use_container_width=True)

else:
    st.error("❌ Unable to fetch data. Please check your internet connection or try again after market opens.")