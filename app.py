import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time as time_module
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="F&O Stock Screener Pro - All Indicators",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .bullish-text { color: #00C853; font-weight: bold; }
    .bearish-text { color: #FF1744; font-weight: bold; }
    .neutral-text { color: #FFD700; }
    .metric-card {
        background: linear-gradient(135deg, #1E1E1E 0%, #2A2A2A 100%);
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #333;
        margin: 8px 0;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateX(5px);
        border-color: #555;
    }
    .strong-bullish { border-left: 5px solid #00C853; }
    .moderate-bullish { border-left: 5px solid #69F0AE; }
    .strong-bearish { border-left: 5px solid #FF1744; }
    .moderate-bearish { border-left: 5px solid #FF5252; }
    .indicator-tag {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 15px;
        margin: 3px;
        font-size: 13px;
        font-weight: 500;
    }
    .tag-bullish { background: rgba(0,200,83,0.2); color: #00C853; border: 1px solid #00C853; }
    .tag-bearish { background: rgba(255,23,68,0.2); color: #FF1744; border: 1px solid #FF1744; }
    .tag-neutral { background: rgba(255,215,0,0.2); color: #FFD700; border: 1px solid #FFD700; }
    .tag-oi { background: rgba(100,149,237,0.2); color: #6495ED; border: 1px solid #6495ED; }
    .tag-ichimoku { background: rgba(255,105,180,0.2); color: #FF69B4; border: 1px solid #FF69B4; }
    .tag-vwap { background: rgba(0,255,255,0.2); color: #00FFFF; border: 1px solid #00FFFF; }
    .tag-liquidity { background: rgba(255,165,0,0.2); color: #FFA500; border: 1px solid #FFA500; }
    .score-badge {
        font-size: 18px;
        font-weight: bold;
        padding: 5px 15px;
        border-radius: 20px;
        text-align: center;
    }
    .score-high { background: linear-gradient(135deg, #00C853, #69F0AE); color: #000; }
    .score-medium { background: linear-gradient(135deg, #FFD700, #FFA000); color: #000; }
    .scan-button {
        background: linear-gradient(135deg, #FF6B6B, #FF1744);
        color: white;
        padding: 15px 30px;
        border: none;
        border-radius: 10px;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
        transition: transform 0.2s;
    }
    .scan-button:hover { transform: scale(1.05); }
    .indicator-row {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        margin: 10px 0;
    }
    .indicator-item {
        text-align: center;
        padding: 8px;
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
    }
    .indicator-label {
        font-size: 10px;
        color: #888;
        text-transform: uppercase;
    }
    .indicator-value {
        font-size: 16px;
        font-weight: bold;
        margin-top: 4px;
    }
    .liquidity-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: bold;
    }
    .liquidity-high { background: rgba(0,200,83,0.2); color: #00C853; }
    .liquidity-medium { background: rgba(255,215,0,0.2); color: #FFD700; }
    .liquidity-low { background: rgba(255,23,68,0.2); color: #FF1744; }
    .market-status {
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin: 10px 0;
    }
    .market-open { background: rgba(0,200,83,0.2); color: #00C853; border: 1px solid #00C853; }
    .market-closed { background: rgba(255,215,0,0.2); color: #FFD700; border: 1px solid #FFD700; }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("📊 F&O Stock Screener Pro - Complete Indicator Suite")
st.markdown("### 📈 RSI • MACD • EMA • ADX • VWAP • AVWAP • Ichimoku • Supertrend • Bollinger • OI • Liquidity Filter")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    current_time = datetime.now()
    
    # Market Status
    market_hours = (9, 15)  # 9:15 AM
    market_close = (15, 30)  # 3:30 PM
    current_hour = current_time.hour
    current_minute = current_time.minute
    
    is_market_open = (
        (current_hour > market_hours[0] or (current_hour == market_hours[0] and current_minute >= market_hours[1])) and
        (current_hour < market_close[0] or (current_hour == market_close[0] and current_minute <= market_close[1]))
    ) and current_time.weekday() < 5  # Monday to Friday
    
    if is_market_open:
        st.markdown('<div class="market-status market-open">🟢 MARKET OPEN - Live Data</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="market-status market-closed">🟡 MARKET CLOSED - Latest Available Data</div>', unsafe_allow_html=True)
    
    st.info(f"🕐 {current_time.strftime('%H:%M:%S')} IST | {current_time.strftime('%d-%b-%Y')} ({current_time.strftime('%A')})")
    
    st.markdown("---")
    
    # ===== MANUAL SCAN BUTTON =====
    st.markdown("### 🔍 Scan Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 RUN SCAN NOW", use_container_width=True, type="primary"):
            st.cache_data.clear()  # Clear cache for fresh data
            st.rerun()
    
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-scan", value=False)
        if auto_refresh:
            refresh_interval = st.selectbox("Every", [60, 120, 300, 600], index=1, format_func=lambda x: f"{x//60} min" if x >= 60 else f"{x}s")
    
    st.markdown("---")
    
    # ===== LIQUIDITY FILTER =====
    st.markdown("### 💧 Liquidity Filter")
    
    liquidity_level = st.select_slider(
        "Minimum Liquidity",
        options=["Low", "Medium", "High", "Ultra High"],
        value="Medium",
        help="Filter stocks based on volume and OI liquidity"
    )
    
    # Map to thresholds
    liquidity_thresholds = {
        "Low": {"min_volume": 50000, "min_oi": 100000, "min_volume_ratio": 0.5},
        "Medium": {"min_volume": 200000, "min_oi": 500000, "min_volume_ratio": 1.0},
        "High": {"min_volume": 1000000, "min_oi": 2000000, "min_volume_ratio": 1.5},
        "Ultra High": {"min_volume": 5000000, "min_oi": 10000000, "min_volume_ratio": 2.0},
    }
    
    liq_config = liquidity_thresholds[liquidity_level]
    
    st.markdown(f"""
        <div style="background:rgba(255,165,0,0.1); padding:10px; border-radius:8px; border:1px solid #FFA500;">
            <small>
            <b>Min Volume:</b> {liq_config['min_volume']:,}<br>
            <b>Min OI:</b> {liq_config['min_oi']:,}<br>
            <b>Min Vol Ratio:</b> {liq_config['min_volume_ratio']}x
            </small>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Indicator Parameters in Tabs
    st.subheader("📊 Indicator Settings")
    
    tabs = st.tabs(["📈 Trend", "📐 Momentum", "📏 VWAP/BB", "🌸 Ichimoku"])
    
    with tabs[0]:
        ema_period = st.slider("EMA Period", 10, 50, 20)
        adx_period = st.slider("ADX Period", 10, 20, 14)
        adx_threshold = st.slider("ADX Threshold", 15, 35, 25)
        st.markdown("---")
        st_period = st.slider("Supertrend Period", 7, 14, 10)
        st_multiplier = st.slider("ST Multiplier", 1.0, 5.0, 3.0, 0.5)
    
    with tabs[1]:
        rsi_period = st.slider("RSI Period", 7, 21, 14)
        rsi_oversold = st.slider("Oversold Level", 20, 40, 30)
        rsi_overbought = st.slider("Overbought Level", 60, 80, 70)
        st.markdown("---")
        macd_fast = st.slider("MACD Fast EMA", 8, 15, 12)
        macd_slow = st.slider("MACD Slow EMA", 20, 30, 26)
        macd_signal = st.slider("MACD Signal", 5, 12, 9)
    
    with tabs[2]:
        st.markdown("**VWAP Settings**")
        vwap_reset = st.selectbox("VWAP Reset", ["Daily", "Weekly", "Monthly"], index=0)
        st.markdown("**Anchored VWAP (AVWAP)**")
        avwap_date = st.date_input("AVWAP Anchor Date", value=datetime.now() - timedelta(days=5))
        st.markdown("---")
        bb_period = st.slider("Bollinger Period", 10, 30, 20)
        bb_std = st.slider("BB Std Dev", 1.0, 3.0, 2.0, 0.5)
    
    with tabs[3]:
        st.markdown("**Ichimoku Cloud**")
        ichi_conversion = st.slider("Tenkan-sen", 7, 12, 9)
        ichi_base = st.slider("Kijun-sen", 20, 30, 26)
        ichi_span_b = st.slider("Senkou Span B", 40, 60, 52)
        ichi_displacement = st.slider("Displacement", 20, 30, 26)
    
    st.markdown("---")
    
    # Other Filters
    st.subheader("🎯 Signal Filters")
    min_volume_ratio = st.slider("Signal Volume Ratio", 1.0, 5.0, 1.5, 0.1)
    min_oi_change = st.slider("Signal OI Change %", 1.0, 20.0, 5.0, 1.0)
    
    st.markdown("---")
    st.caption(f"Data: Yahoo Finance + NSE")
    st.caption(f"Scan Mode: {'Live Intraday' if is_market_open else 'Latest Available'}")

# F&O Stock List with Liquidity Classification
@st.cache_data(ttl=300)
def get_fno_stocks_with_liquidity():
    """F&O stocks with liquidity tiers"""
    stocks = {
        # Ultra High Liquidity (Tier 1)
        "RELIANCE.NS": {"name": "Reliance Industries", "sector": "Oil & Gas", "liquidity": "Ultra High"},
        "HDFCBANK.NS": {"name": "HDFC Bank", "sector": "Banking", "liquidity": "Ultra High"},
        "ICICIBANK.NS": {"name": "ICICI Bank", "sector": "Banking", "liquidity": "Ultra High"},
        "INFY.NS": {"name": "Infosys", "sector": "IT", "liquidity": "Ultra High"},
        "TCS.NS": {"name": "TCS", "sector": "IT", "liquidity": "Ultra High"},
        "SBIN.NS": {"name": "SBI", "sector": "Banking", "liquidity": "Ultra High"},
        "BHARTIARTL.NS": {"name": "Bharti Airtel", "sector": "Telecom", "liquidity": "Ultra High"},
        
        # High Liquidity (Tier 2)
        "KOTAKBANK.NS": {"name": "Kotak Mahindra", "sector": "Banking", "liquidity": "High"},
        "ITC.NS": {"name": "ITC", "sector": "FMCG", "liquidity": "High"},
        "LT.NS": {"name": "L&T", "sector": "Infrastructure", "liquidity": "High"},
        "AXISBANK.NS": {"name": "Axis Bank", "sector": "Banking", "liquidity": "High"},
        "MARUTI.NS": {"name": "Maruti Suzuki", "sector": "Auto", "liquidity": "High"},
        "HINDUNILVR.NS": {"name": "HUL", "sector": "FMCG", "liquidity": "High"},
        "BAJFINANCE.NS": {"name": "Bajaj Finance", "sector": "NBFC", "liquidity": "High"},
        "SUNPHARMA.NS": {"name": "Sun Pharma", "sector": "Pharma", "liquidity": "High"},
        "TITAN.NS": {"name": "Titan", "sector": "Consumer", "liquidity": "High"},
        "TATASTEEL.NS": {"name": "Tata Steel", "sector": "Metal", "liquidity": "High"},
        "TATAMOTORS.NS": {"name": "Tata Motors", "sector": "Auto", "liquidity": "High"},
        "M&M.NS": {"name": "M&M", "sector": "Auto", "liquidity": "High"},
        "NTPC.NS": {"name": "NTPC", "sector": "Power", "liquidity": "High"},
        "POWERGRID.NS": {"name": "Power Grid", "sector": "Power", "liquidity": "High"},
        
        # Medium Liquidity (Tier 3)
        "ADANIPORTS.NS": {"name": "Adani Ports", "sector": "Infrastructure", "liquidity": "Medium"},
        "ADANIENT.NS": {"name": "Adani Enterprises", "sector": "Diversified", "liquidity": "Medium"},
        "ASIANPAINT.NS": {"name": "Asian Paints", "sector": "Consumer", "liquidity": "Medium"},
        "HCLTECH.NS": {"name": "HCL Tech", "sector": "IT", "liquidity": "Medium"},
        "WIPRO.NS": {"name": "Wipro", "sector": "IT", "liquidity": "Medium"},
        "TECHM.NS": {"name": "Tech Mahindra", "sector": "IT", "liquidity": "Medium"},
        "ULTRACEMCO.NS": {"name": "UltraTech Cement", "sector": "Cement", "liquidity": "Medium"},
        "JSWSTEEL.NS": {"name": "JSW Steel", "sector": "Metal", "liquidity": "Medium"},
        "GRASIM.NS": {"name": "Grasim", "sector": "Cement", "liquidity": "Medium"},
        "BAJAJFINSV.NS": {"name": "Bajaj Finserv", "sector": "NBFC", "liquidity": "Medium"},
        "BAJAJ-AUTO.NS": {"name": "Bajaj Auto", "sector": "Auto", "liquidity": "Medium"},
        "NESTLEIND.NS": {"name": "Nestle India", "sector": "FMCG", "liquidity": "Medium"},
        "DRREDDY.NS": {"name": "Dr. Reddy's", "sector": "Pharma", "liquidity": "Medium"},
        "CIPLA.NS": {"name": "Cipla", "sector": "Pharma", "liquidity": "Medium"},
        "BPCL.NS": {"name": "BPCL", "sector": "Oil & Gas", "liquidity": "Medium"},
        "ONGC.NS": {"name": "ONGC", "sector": "Oil & Gas", "liquidity": "Medium"},
        "COALINDIA.NS": {"name": "Coal India", "sector": "Mining", "liquidity": "Medium"},
        "HDFCLIFE.NS": {"name": "HDFC Life", "sector": "Insurance", "liquidity": "Medium"},
        "SBILIFE.NS": {"name": "SBI Life", "sector": "Insurance", "liquidity": "Medium"},
        "DIVISLAB.NS": {"name": "Divi's Lab", "sector": "Pharma", "liquidity": "Medium"},
        "APOLLOHOSP.NS": {"name": "Apollo Hospitals", "sector": "Healthcare", "liquidity": "Medium"},
        "EICHERMOT.NS": {"name": "Eicher Motors", "sector": "Auto", "liquidity": "Medium"},
        "BRITANNIA.NS": {"name": "Britannia", "sector": "FMCG", "liquidity": "Medium"},
        "HEROMOTOCO.NS": {"name": "Hero MotoCorp", "sector": "Auto", "liquidity": "Medium"},
        "HINDALCO.NS": {"name": "Hindalco", "sector": "Metal", "liquidity": "Medium"},
        "UPL.NS": {"name": "UPL", "sector": "Agrochem", "liquidity": "Medium"},
        "INDUSINDBK.NS": {"name": "IndusInd Bank", "sector": "Banking", "liquidity": "Medium"},
        "TATACONSUM.NS": {"name": "Tata Consumer", "sector": "FMCG", "liquidity": "Medium"},
        "SHREECEM.NS": {"name": "Shree Cement", "sector": "Cement", "liquidity": "Medium"},
    }
    return stocks

def filter_by_liquidity(stocks_dict, level):
    """Filter stocks based on liquidity tier"""
    liquidity_order = ["Low", "Medium", "High", "Ultra High"]
    min_index = liquidity_order.index(level)
    
    filtered = {}
    for symbol, info in stocks_dict.items():
        stock_liq_index = liquidity_order.index(info['liquidity'])
        if stock_liq_index >= min_index:
            filtered[symbol] = info
    
    return filtered

# ===================== TECHNICAL INDICATORS =====================

def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df, fast=12, slow=26, signal=9):
    exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_adx(df, period=14):
    high, low, close = df['High'], df['Low'], df['Close']
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    plus_dm.iloc[0] = 0
    minus_dm.iloc[0] = 0
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx, plus_di, minus_di

def calculate_supertrend(df, period=10, multiplier=3):
    high, low, close = df['High'], df['Low'], df['Close']
    hl2 = (high + low) / 2
    atr = (high - low).rolling(window=period).mean()
    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr
    supertrend = pd.Series(1, index=df.index)
    for i in range(period, len(df)):
        if close.iloc[i] > upper_band.iloc[i-1]:
            supertrend.iloc[i] = 1
        elif close.iloc[i] < lower_band.iloc[i-1]:
            supertrend.iloc[i] = -1
        else:
            supertrend.iloc[i] = supertrend.iloc[i-1]
    return supertrend

def calculate_bollinger_bands(df, period=20, std_dev=2):
    sma = df['Close'].rolling(window=period).mean()
    std = df['Close'].rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    bandwidth = ((upper_band - lower_band) / sma) * 100
    return upper_band, lower_band, bandwidth

def calculate_vwap(df):
    df = df.copy()
    df['Date'] = df.index.date
    vwap_values = []
    for date in df['Date'].unique():
        day_data = df[df['Date'] == date]
        typical_price = (day_data['High'] + day_data['Low'] + day_data['Close']) / 3
        cumulative_pv = (typical_price * day_data['Volume']).cumsum()
        cumulative_volume = day_data['Volume'].cumsum()
        day_vwap = cumulative_pv / cumulative_volume
        vwap_values.extend(day_vwap.values)
    return pd.Series(vwap_values, index=df.index)

def calculate_anchored_vwap(df, anchor_date):
    df = df.copy()
    anchor_datetime = pd.Timestamp(anchor_date)
    df_anchored = df[df.index >= anchor_datetime]
    if len(df_anchored) < 2:
        return pd.Series(df['Close'].iloc[-1], index=df.index)
    typical_price = (df_anchored['High'] + df_anchored['Low'] + df_anchored['Close']) / 3
    cumulative_pv = (typical_price * df_anchored['Volume']).cumsum()
    cumulative_volume = df_anchored['Volume'].cumsum()
    avwap_anchored = cumulative_pv / cumulative_volume
    full_avwap = pd.Series(index=df.index)
    full_avwap[df_anchored.index] = avwap_anchored
    full_avwap = full_avwap.ffill()
    return full_avwap

def calculate_ichimoku(df, tenkan_period=9, kijun_period=26, senkou_b_period=52, displacement=26):
    tenkan_high = df['High'].rolling(window=tenkan_period).max()
    tenkan_low = df['Low'].rolling(window=tenkan_period).min()
    tenkan_sen = (tenkan_high + tenkan_low) / 2
    kijun_high = df['High'].rolling(window=kijun_period).max()
    kijun_low = df['Low'].rolling(window=kijun_period).min()
    kijun_sen = (kijun_high + kijun_low) / 2
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
    senkou_high = df['High'].rolling(window=senkou_b_period).max()
    senkou_low = df['Low'].rolling(window=senkou_b_period).min()
    senkou_span_b = ((senkou_high + senkou_low) / 2).shift(displacement)
    chikou_span = df['Close'].shift(-displacement)
    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b,
        'chikou_span': chikou_span,
        'cloud_green': senkou_span_a > senkou_span_b,
    }

@st.cache_data(ttl=120)
def fetch_stock_data(symbol, stock_name, sector, liquidity_tier):
    """Fetch and analyze stock data with ALL indicators"""
    try:
        stock = yf.Ticker(symbol)
        # Use 1mo data for Ichimoku, works for both live and post-market
        df = stock.history(period='1mo', interval='5m')
        
        if df.empty or len(df) < 100:
            return None
        
        # Price data
        current_price = df['Close'].iloc[-1]
        open_price = df['Open'].iloc[0]
        day_high = df['High'].max()
        day_low = df['Low'].min()
        daily_change = ((current_price - open_price) / open_price) * 100
        
        # Volume - Check liquidity
        current_volume = df['Volume'].iloc[-1]
        avg_volume = df['Volume'].rolling(window=20).mean().iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Get OI data
        try:
            fut_symbol = symbol.replace('.NS', '') + 'FUT.NS'
            fut = yf.Ticker(fut_symbol)
            fut_info = fut.info
            oi = fut_info.get('openInterest', 0)
            prev_oi = fut_info.get('previousOpenInterest', oi)
            oi_change = ((oi - prev_oi) / prev_oi * 100) if prev_oi > 0 else 0
        except:
            oi = 0
            oi_change = 0
        
        # ===== LIQUIDITY CHECK =====
        # Filter out low liquidity stocks
        if current_volume < liq_config['min_volume'] or (oi > 0 and oi < liq_config['min_oi']):
            return None
        
        # ===== CALCULATE INDICATORS =====
        rsi_series = calculate_rsi(df, rsi_period)
        current_rsi = rsi_series.iloc[-1]
        prev_rsi = rsi_series.iloc[-2] if len(rsi_series) > 1 else current_rsi
        rsi_trend = "⬆️ Rising" if current_rsi > prev_rsi else "⬇️ Falling"
        
        macd_line, signal_line, histogram = calculate_macd(df, macd_fast, macd_slow, macd_signal)
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_histogram = histogram.iloc[-1]
        macd_bullish = current_macd > current_signal
        macd_cross = "🟢 Bullish" if macd_bullish else "🔴 Bearish"
        
        ema = df['Close'].ewm(span=ema_period, adjust=False).mean()
        current_ema = ema.iloc[-1]
        price_vs_ema_pct = ((current_price - current_ema) / current_ema) * 100
        ema_bullish = current_price > current_ema
        ema_status = f"⬆️ Above (+{price_vs_ema_pct:.1f}%)" if ema_bullish else f"⬇️ Below ({price_vs_ema_pct:.1f}%)"
        
        adx_series, plus_di, minus_di = calculate_adx(df, adx_period)
        current_adx = adx_series.iloc[-1]
        current_plus_di = plus_di.iloc[-1]
        current_minus_di = minus_di.iloc[-1]
        adx_strong = current_adx > adx_threshold
        adx_bullish = current_plus_di > current_minus_di
        
        if adx_strong:
            adx_status = f"🔥 Strong {'Bullish' if adx_bullish else 'Bearish'}"
        else:
            adx_status = "😴 Weak/Ranging"
        
        vwap_series = calculate_vwap(df)
        current_vwap = vwap_series.iloc[-1]
        price_vs_vwap_pct = ((current_price - current_vwap) / current_vwap) * 100
        vwap_bullish = current_price > current_vwap
        
        avwap_series = calculate_anchored_vwap(df, avwap_date)
        current_avwap = avwap_series.iloc[-1]
        price_vs_avwap_pct = ((current_price - current_avwap) / current_avwap) * 100 if current_avwap > 0 else 0
        avwap_bullish = current_price > current_avwap
        
        ichimoku = calculate_ichimoku(df, ichi_conversion, ichi_base, ichi_span_b, ichi_displacement)
        current_tenkan = ichimoku['tenkan_sen'].iloc[-1]
        current_kijun = ichimoku['kijun_sen'].iloc[-1]
        cloud_bullish = ichimoku['cloud_green'].iloc[-1]
        current_cloud_a = ichimoku['senkou_span_a'].iloc[-1]
        current_cloud_b = ichimoku['senkou_span_b'].iloc[-1]
        
        tk_cross = current_tenkan > current_kijun
        price_above_cloud = current_price > max(current_cloud_a, current_cloud_b) if not pd.isna(current_cloud_a) else False
        price_below_cloud = current_price < min(current_cloud_a, current_cloud_b) if not pd.isna(current_cloud_a) else False
        price_in_cloud = not price_above_cloud and not price_below_cloud
        
        if price_above_cloud and tk_cross and cloud_bullish:
            ichi_signal = "🌸 Strong Bullish"
        elif price_below_cloud and not tk_cross and not cloud_bullish:
            ichi_signal = "🌸 Strong Bearish"
        elif price_in_cloud:
            ichi_signal = "🌸 In Cloud (Neutral)"
        elif tk_cross:
            ichi_signal = "🌸 Bullish TK Cross"
        else:
            ichi_signal = "🌸 Bearish TK Cross"
        
        st_series = calculate_supertrend(df, st_period, st_multiplier)
        supertrend_bullish = st_series.iloc[-1] == 1
        st_signal = "🟢 BUY" if supertrend_bullish else "🔴 SELL"
        
        bb_upper, bb_lower, bb_width = calculate_bollinger_bands(df, bb_period, bb_std)
        current_bb_upper = bb_upper.iloc[-1]
        current_bb_lower = bb_lower.iloc[-1]
        current_bb_width = bb_width.iloc[-1]
        bb_position = ((current_price - current_bb_lower) / (current_bb_upper - current_bb_lower)) * 100 if (current_bb_upper - current_bb_lower) > 0 else 50
        
        if bb_position > 100:
            bb_signal = "🚀 Above Upper"
        elif bb_position < 0:
            bb_signal = "📉 Below Lower"
        elif bb_position > 80:
            bb_signal = "⬆️ Near Upper"
        elif bb_position < 20:
            bb_signal = "⬇️ Near Lower"
        else:
            bb_signal = "↔️ Middle"
        
        # Determine liquidity color
        liq_map = {"Ultra High": "liquidity-high", "High": "liquidity-high", "Medium": "liquidity-medium"}
        liq_color = liq_map.get(liquidity_tier, "liquidity-medium")
        
        return {
            'symbol': symbol.replace('.NS', ''),
            'name': stock_name,
            'sector': sector,
            'liquidity': liquidity_tier,
            'liq_color': liq_color,
            'price': current_price,
            'open': open_price,
            'high': day_high,
            'low': day_low,
            'change_pct': daily_change,
            'volume': current_volume,
            'avg_volume': avg_volume,
            'volume_ratio': volume_ratio,
            'oi': oi,
            'rsi': current_rsi,
            'rsi_trend': rsi_trend,
            'macd': current_macd,
            'macd_signal': current_signal,
            'macd_histogram': current_histogram,
            'macd_bullish': macd_bullish,
            'macd_cross': macd_cross,
            'ema': current_ema,
            'price_vs_ema_pct': price_vs_ema_pct,
            'ema_bullish': ema_bullish,
            'ema_status': ema_status,
            'adx': current_adx,
            'plus_di': current_plus_di,
            'minus_di': current_minus_di,
            'adx_strong': adx_strong,
            'adx_bullish': adx_bullish,
            'adx_status': adx_status,
            'vwap': current_vwap,
            'price_vs_vwap_pct': price_vs_vwap_pct,
            'vwap_bullish': vwap_bullish,
            'avwap': current_avwap,
            'price_vs_avwap_pct': price_vs_avwap_pct,
            'avwap_bullish': avwap_bullish,
            'tenkan_sen': current_tenkan,
            'kijun_sen': current_kijun,
            'cloud_bullish': cloud_bullish,
            'tk_cross': tk_cross,
            'price_above_cloud': price_above_cloud,
            'price_below_cloud': price_below_cloud,
            'price_in_cloud': price_in_cloud,
            'ichi_signal': ichi_signal,
            'supertrend_bullish': supertrend_bullish,
            'st_signal': st_signal,
            'bb_upper': current_bb_upper,
            'bb_lower': current_bb_lower,
            'bb_position': bb_position,
            'bb_width': current_bb_width,
            'bb_signal': bb_signal,
            'oi_change_pct': oi_change,
        }
    except Exception as e:
        return None

def calculate_score(data):
    """Calculate composite bullish/bearish scores (max 15)"""
    bullish = 0
    bearish = 0
    
    if rsi_oversold <= data['rsi'] <= 60 and data['rsi_trend'] == "⬆️ Rising":
        bullish += 2
    elif data['rsi'] > rsi_overbought:
        bearish += 1
    if 40 <= data['rsi'] <= rsi_overbought and data['rsi_trend'] == "⬇️ Falling":
        bearish += 2
    elif data['rsi'] < rsi_oversold:
        bullish += 1
    
    if data['macd_bullish']:
        bullish += 2
        if data['macd_histogram'] > 0:
            bullish += 1
    else:
        bearish += 2
        if data['macd_histogram'] < 0:
            bearish += 1
    
    if data['ema_bullish']:
        bullish += 1
    else:
        bearish += 1
    
    if data['adx_strong']:
        if data['adx_bullish']:
            bullish += 2
        else:
            bearish += 2
    
    if data['vwap_bullish']:
        bullish += 1
    else:
        bearish += 1
    
    if data['avwap_bullish']:
        bullish += 1
    else:
        bearish += 1
    
    if data['price_above_cloud'] and data['tk_cross'] and data['cloud_bullish']:
        bullish += 2
    elif data['price_below_cloud'] and not data['tk_cross'] and not data['cloud_bullish']:
        bearish += 2
    elif data['tk_cross']:
        bullish += 1
    elif not data['tk_cross']:
        bearish += 1
    
    if data['supertrend_bullish']:
        bullish += 1
    else:
        bearish += 1
    
    if data['volume_ratio'] > min_volume_ratio:
        if data['change_pct'] > 0:
            bullish += 1
        else:
            bearish += 1
    
    if data['oi_change_pct'] > min_oi_change:
        if data['change_pct'] > 0:
            bullish += 2
        else:
            bearish += 1
    elif data['oi_change_pct'] < -min_oi_change:
        if data['change_pct'] > 0:
            bearish += 1
        else:
            bullish += 1
    
    if data['bb_position'] > 80:
        bullish += 1
    elif data['bb_position'] < 20:
        bearish += 1
    
    return min(bullish, 15), min(bearish, 15)

def get_indicator_tags(data):
    """Generate indicator tags"""
    tags = []
    
    # Liquidity tag
    tags.append((f"💧 {data['liquidity']}", 'tag-liquidity'))
    
    if data['rsi'] < rsi_oversold:
        tags.append(('RSI Oversold', 'tag-bullish'))
    elif data['rsi'] > rsi_overbought:
        tags.append(('RSI Overbought', 'tag-bearish'))
    
    if data['macd_bullish']:
        tags.append(('MACD Bullish', 'tag-bullish'))
    else:
        tags.append(('MACD Bearish', 'tag-bearish'))
    
    if data['ema_bullish']:
        tags.append(('EMA Above', 'tag-bullish'))
    else:
        tags.append(('EMA Below', 'tag-bearish'))
    
    if data['adx_strong']:
        tags.append((f'ADX Strong', 'tag-bullish' if data['adx_bullish'] else 'tag-bearish'))
    
    if data['vwap_bullish']:
        tags.append(('VWAP Above', 'tag-vwap'))
    else:
        tags.append(('VWAP Below', 'tag-bearish'))
    
    if data['price_above_cloud']:
        tags.append(('Above Cloud', 'tag-ichimoku'))
    elif data['price_below_cloud']:
        tags.append(('Below Cloud', 'tag-ichimoku'))
    
    if data['cloud_bullish']:
        tags.append(('Bullish Cloud', 'tag-ichimoku'))
    
    if data['supertrend_bullish']:
        tags.append(('ST Buy', 'tag-bullish'))
    else:
        tags.append(('ST Sell', 'tag-bearish'))
    
    if abs(data['oi_change_pct']) > min_oi_change:
        if data['oi_change_pct'] > 0:
            tags.append((f'OI ↑{data["oi_change_pct"]:.0f}%', 'tag-oi'))
        else:
            tags.append((f'OI ↓{abs(data["oi_change_pct"]):.0f}%', 'tag-oi'))
    
    return tags

# ===================== MAIN PROCESSING =====================

# Get filtered stocks
all_stocks = get_fno_stocks_with_liquidity()
filtered_stocks = filter_by_liquidity(all_stocks, liquidity_level)

st.info(f"📊 Scanning **{len(filtered_stocks)}** {liquidity_level}+ liquidity F&O stocks...")

# Auto-refresh logic
if auto_refresh:
    time_module.sleep(refresh_interval)
    st.rerun()

# Scan button already handled above

stock_data_list = []

progress_bar = st.progress(0)
status_text = st.empty()

stock_items = list(filtered_stocks.items())
total_stocks = len(stock_items)

for idx, (symbol, info) in enumerate(stock_items):
    status_text.text(f"📊 Scanning {info['name']} ({symbol.replace('.NS', '')}) - {info['liquidity']} Liquidity... ({idx+1}/{total_stocks})")
    data = fetch_stock_data(symbol, info['name'], info['sector'], info['liquidity'])
    
    if data:
        bullish_score, bearish_score = calculate_score(data)
        data['bullish_score'] = bullish_score
        data['bearish_score'] = bearish_score
        data['net_score'] = bullish_score - bearish_score
        stock_data_list.append(data)
    
    progress_bar.progress((idx + 1) / total_stocks)

progress_bar.empty()
status_text.empty()

if stock_data_list:
    df_all = pd.DataFrame(stock_data_list)
    
    # Sort
    df_bullish = df_all[df_all['change_pct'] > 0].nlargest(10, 'bullish_score')
    df_bearish = df_all[df_all['change_pct'] < 0].nlargest(10, 'bearish_score')
    
    # Summary
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📈 Advancers", f"{len(df_all[df_all['change_pct']>0])}/{len(df_all)}")
    with col2:
        st.metric("📉 Decliners", f"{len(df_all[df_all['change_pct']<0])}/{len(df_all)}")
    with col3:
        st.metric("📊 Avg RSI", f"{df_all['rsi'].mean():.1f}")
    with col4:
        vwap_above = len(df_all[df_all['vwap_bullish']])
        st.metric("💎 Above VWAP", f"{vwap_above}/{len(df_all)}")
    with col5:
        ichi_bull = len(df_all[df_all['price_above_cloud']])
        st.metric("🌸 Above Cloud", f"{ichi_bull}/{len(df_all)}")
    
    st.markdown("---")
    
    # ===== TOP 10 BULLISH =====
    st.markdown("## 🟢 Top 10 Bullish Stocks")
    st.markdown("*Filtered by High Liquidity | RSI • MACD • EMA • ADX • VWAP • AVWAP • Ichimoku • Supertrend • BB • OI*")
    st.markdown("---")
    
    for idx, row in df_bullish.iterrows():
        tags = get_indicator_tags(row)
        tags_html = ' '.join([f'<span class="indicator-tag {tag[1]}">{tag[0]}</span>' for tag in tags])
        
        score_class = "score-high" if row['bullish_score'] >= 12 else "score-medium"
        card_class = "strong-bullish" if row['bullish_score'] >= 12 else "moderate-bullish"
        signal = "🔥 STRONG BUY" if row['bullish_score'] >= 12 else "📈 BUY" if row['bullish_score'] >= 8 else "👀 WATCH"
        
        st.markdown(f"""
            <div class="metric-card {card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="margin:0; color: white;">{row['name']} 
                            <small style="color: #888;">({row['symbol']})</small>
                            <span class="liquidity-badge {row['liq_color']}">{row['liquidity']}</span>
                        </h3>
                        <span style="font-size: 12px; color: #888;">{row['sector']} | Vol: {row['volume']/1e6:.2f}M | OI: {row['oi']/1e6:.2f}M</span>
                    </div>
                    <div class="score-badge {score_class}">{signal} - {row['bullish_score']:.0f}/15</div>
                </div>
                
                <div style="margin: 12px 0; display: flex; align-items: baseline; gap: 15px;">
                    <span style="font-size: 28px; font-weight: bold;">₹{row['price']:.2f}</span>
                    <span class="bullish-text" style="font-size: 20px;">{row['change_pct']:+.2f}%</span>
                    <span style="color: #888;">H: ₹{row['high']:.2f} | L: ₹{row['low']:.2f}</span>
                </div>
                
                <div class="indicator-row">
                    <div class="indicator-item">
                        <div class="indicator-label">RSI</div>
                        <div class="indicator-value" style="color: {'#00C853' if 40<=row['rsi']<=60 else '#FF1744' if row['rsi']>70 else '#FFD700'};">{row['rsi']:.0f}</div>
                        <small style="color:#888;font-size:10px;">{row['rsi_trend']}</small>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">MACD</div>
                        <div class="indicator-value" style="color: {'#00C853' if row['macd_bullish'] else '#FF1744'};">{row['macd_cross']}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">EMA</div>
                        <div class="indicator-value" style="color: {'#00C853' if row['ema_bullish'] else '#FF1744'};">{row['ema_status']}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">VWAP</div>
                        <div class="indicator-value" style="color: {'#00FFFF' if row['vwap_bullish'] else '#FF1744'};">₹{row['vwap']:.1f}</div>
                        <small style="color:#888;font-size:10px;">{row['price_vs_vwap_pct']:+.1f}%</small>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">Ichimoku</div>
                        <div class="indicator-value" style="color: #FF69B4; font-size: 12px;">{row['ichi_signal']}</div>
                    </div>
                </div>
                
                <div style="margin-top: 10px;">
                    {tags_html}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== TOP 10 BEARISH =====
    st.markdown("## 🔴 Top 10 Bearish Stocks")
    st.markdown("*Filtered by High Liquidity | RSI • MACD • EMA • ADX • VWAP • AVWAP • Ichimoku • Supertrend • BB • OI*")
    st.markdown("---")
    
    for idx, row in df_bearish.iterrows():
        tags = get_indicator_tags(row)
        tags_html = ' '.join([f'<span class="indicator-tag {tag[1]}">{tag[0]}</span>' for tag in tags])
        
        score_class = "score-high" if row['bearish_score'] >= 12 else "score-medium"
        card_class = "strong-bearish" if row['bearish_score'] >= 12 else "moderate-bearish"
        signal = "🔥 STRONG SELL" if row['bearish_score'] >= 12 else "📉 SELL" if row['bearish_score'] >= 8 else "👀 WATCH"
        
        st.markdown(f"""
            <div class="metric-card {card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="margin:0; color: white;">{row['name']} 
                            <small style="color: #888;">({row['symbol']})</small>
                            <span class="liquidity-badge {row['liq_color']}">{row['liquidity']}</span>
                        </h3>
                        <span style="font-size: 12px; color: #888;">{row['sector']} | Vol: {row['volume']/1e6:.2f}M | OI: {row['oi']/1e6:.2f}M</span>
                    </div>
                    <div class="score-badge {score_class}">{signal} - {row['bearish_score']:.0f}/15</div>
                </div>
                
                <div style="margin: 12px 0; display: flex; align-items: baseline; gap: 15px;">
                    <span style="font-size: 28px; font-weight: bold;">₹{row['price']:.2f}</span>
                    <span class="bearish-text" style="font-size: 20px;">{row['change_pct']:+.2f}%</span>
                    <span style="color: #888;">H: ₹{row['high']:.2f} | L: ₹{row['low']:.2f}</span>
                </div>
                
                <div class="indicator-row">
                    <div class="indicator-item">
                        <div class="indicator-label">RSI</div>
                        <div class="indicator-value" style="color: {'#FF1744' if 40<=row['rsi']<=60 else '#00C853' if row['rsi']<30 else '#FFD700'};">{row['rsi']:.0f}</div>
                        <small style="color:#888;font-size:10px;">{row['rsi_trend']}</small>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">MACD</div>
                        <div class="indicator-value" style="color: {'#00C853' if row['macd_bullish'] else '#FF1744'};">{row['macd_cross']}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">EMA</div>
                        <div class="indicator-value" style="color: {'#00C853' if row['ema_bullish'] else '#FF1744'};">{row['ema_status']}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">VWAP</div>
                        <div class="indicator-value" style="color: {'#00FFFF' if row['vwap_bullish'] else '#FF1744'};">₹{row['vwap']:.1f}</div>
                        <small style="color:#888;font-size:10px;">{row['price_vs_vwap_pct']:+.1f}%</small>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">Ichimoku</div>
                        <div class="indicator-value" style="color: #FF69B4; font-size: 12px;">{row['ichi_signal']}</div>
                    </div>
                </div>
                
                <div style="margin-top: 10px;">
                    {tags_html}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Download buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("📥 All Data CSV", df_all.to_csv(index=False), f"fno_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
    with col2:
        st.download_button("📥 Bullish Picks", df_bullish.to_csv(index=False), f"bullish_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
    with col3:
        st.download_button("📥 Bearish Picks", df_bearish.to_csv(index=False), f"bearish_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
    
    # Full data
    with st.expander("📋 Complete Data Table"):
        display_cols = ['name', 'symbol', 'liquidity', 'price', 'change_pct', 'rsi', 'macd_bullish', 
                       'ema_bullish', 'adx', 'vwap_bullish', 'price_above_cloud', 
                       'supertrend_bullish', 'volume_ratio', 'oi_change_pct', 'bullish_score', 'bearish_score']
        st.dataframe(df_all[display_cols].sort_values('net_score', ascending=False), use_container_width=True)

else:
    st.warning("⚠️ No stocks passed the liquidity filter. Try lowering the liquidity threshold.")
    st.info("💡 Click 'RUN SCAN NOW' to retry or lower the liquidity level in sidebar settings.")

st.markdown("---")
st.caption("⚠️ Educational purposes only. Works anytime - Live market or Post-market with latest available data.")
