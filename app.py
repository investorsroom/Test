import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import time as time_module
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="F&O Stock Screener Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .bullish-text { color: #00C853; font-weight: bold; }
    .bearish-text { color: #FF1744; font-weight: bold; }
    .metric-card {
        background: linear-gradient(135deg, #1E1E1E 0%, #2A2A2A 100%);
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #333;
        margin: 8px 0;
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
        font-size: 12px;
        font-weight: 500;
    }
    .tag-bullish { background: rgba(0,200,83,0.2); color: #00C853; border: 1px solid #00C853; }
    .tag-bearish { background: rgba(255,23,68,0.2); color: #FF1744; border: 1px solid #FF1744; }
    .tag-neutral { background: rgba(255,215,0,0.2); color: #FFD700; border: 1px solid #FFD700; }
    .tag-oi { background: rgba(100,149,237,0.2); color: #6495ED; border: 1px solid #6495ED; }
    .tag-ichimoku { background: rgba(255,105,180,0.2); color: #FF69B4; border: 1px solid #FF69B4; }
    .tag-vwap { background: rgba(0,255,255,0.2); color: #00FFFF; border: 1px solid #00FFFF; }
    .score-badge {
        font-size: 16px;
        font-weight: bold;
        padding: 5px 15px;
        border-radius: 20px;
        text-align: center;
    }
    .score-high { background: linear-gradient(135deg, #00C853, #69F0AE); color: #000; }
    .score-medium { background: linear-gradient(135deg, #FFD700, #FFA000); color: #000; }
    .indicator-row {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
        margin: 8px 0;
    }
    .indicator-item {
        text-align: center;
        padding: 6px;
        background: rgba(255,255,255,0.05);
        border-radius: 6px;
    }
    .indicator-label { font-size: 10px; color: #888; text-transform: uppercase; }
    .indicator-value { font-size: 14px; font-weight: bold; margin-top: 3px; }
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

st.title("📊 NSE F&O Stock Screener - Complete Indicator Suite")
st.markdown("### 📈 All NSE F&O Stocks | RSI • MACD • EMA • ADX • VWAP • AVWAP • Ichimoku • Supertrend • BB • OI")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    current_time = datetime.now()
    
    # Market Status
    market_start = (9, 15)
    market_end = (15, 30)
    ch = current_time.hour
    cm = current_time.minute
    wd = current_time.weekday()
    
    is_market_open = (wd < 5 and 
        ((ch > market_start[0] or (ch == market_start[0] and cm >= market_start[1])) and
         (ch < market_end[0] or (ch == market_end[0] and cm <= market_end[1]))))
    
    if is_market_open:
        st.markdown('<div class="market-status market-open">🟢 MARKET OPEN - Live</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="market-status market-closed">🟡 MARKET CLOSED - Latest Data</div>', unsafe_allow_html=True)
    
    st.info(f"🕐 {current_time.strftime('%H:%M:%S')} IST | {current_time.strftime('%d-%b-%Y')}")
    st.markdown("---")
    
    # Scan Button
    st.markdown("### 🔍 Scan Controls")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 RUN SCAN NOW", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        auto_refresh = st.checkbox("Auto-scan", value=False)
        if auto_refresh:
            refresh_interval = st.selectbox("Every", [60, 120, 300], index=1, format_func=lambda x: f"{x//60} min")
    
    st.markdown("---")
    
    # Liquidity Filter
    st.markdown("### 💧 Liquidity Filter")
    min_volume = st.number_input("Min Volume (shares)", min_value=10000, max_value=10000000, value=100000, step=50000, format="%d")
    min_volume_ratio = st.slider("Min Volume Ratio", 0.5, 3.0, 1.0, 0.1)
    
    st.markdown("---")
    
    # Indicator Settings
    st.subheader("📊 Indicator Parameters")
    
    tab1, tab2, tab3 = st.tabs(["Trend", "Momentum", "Advanced"])
    
    with tab1:
        ema_period = st.slider("EMA Period", 10, 50, 20)
        adx_period = st.slider("ADX Period", 10, 20, 14)
        adx_threshold = st.slider("ADX Threshold", 15, 35, 25)
        st_period = st.slider("Supertrend Period", 7, 14, 10)
        st_multiplier = st.slider("ST Multiplier", 1.0, 5.0, 3.0, 0.5)
    
    with tab2:
        rsi_period = st.slider("RSI Period", 7, 21, 14)
        rsi_oversold = st.slider("Oversold", 20, 40, 30)
        rsi_overbought = st.slider("Overbought", 60, 80, 70)
        macd_fast = st.slider("MACD Fast", 8, 15, 12)
        macd_slow = st.slider("MACD Slow", 20, 30, 26)
        macd_signal = st.slider("MACD Signal", 5, 12, 9)
    
    with tab3:
        bb_period = st.slider("BB Period", 10, 30, 20)
        bb_std = st.slider("BB Std Dev", 1.0, 3.0, 2.0, 0.5)
        ichi_conv = st.slider("Ichimoku Tenkan", 7, 12, 9)
        ichi_base = st.slider("Ichimoku Kijun", 20, 30, 26)
        ichi_span = st.slider("Ichimoku Span B", 40, 60, 52)
    
    st.markdown("---")
    min_oi_change = st.slider("OI Change Filter %", 1, 20, 5)
    
    st.caption("Data: Yahoo Finance | Works 24/7")

# ===================== COMPLETE NSE F&O STOCK LIST =====================
@st.cache_data(ttl=3600)
def get_all_fno_stocks():
    """Complete list of all NSE F&O stocks (~185 stocks)"""
    stocks = [
        # NIFTY 50
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS",
        "LT.NS", "BAJFINANCE.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS",
        "TITAN.NS", "ASIANPAINT.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS",
        "ULTRACEMCO.NS", "NTPC.NS", "POWERGRID.NS", "M&M.NS", "TATAMOTORS.NS",
        "TATASTEEL.NS", "JSWSTEEL.NS", "GRASIM.NS", "ADANIPORTS.NS", "ADANIENT.NS",
        "BAJAJFINSV.NS", "BAJAJ-AUTO.NS", "NESTLEIND.NS", "DRREDDY.NS", "CIPLA.NS",
        "BPCL.NS", "ONGC.NS", "COALINDIA.NS", "HDFCLIFE.NS", "SBILIFE.NS",
        "DIVISLAB.NS", "APOLLOHOSP.NS", "EICHERMOT.NS", "BRITANNIA.NS",
        "HEROMOTOCO.NS", "HINDALCO.NS", "UPL.NS", "INDUSINDBK.NS", "TATACONSUM.NS",
        "SHREECEM.NS",
        # Additional F&O Stocks
        "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ACC.NS",
        "ADANIENSOL.NS", "ADANIGREEN.NS", "ADANITRANS.NS", "ALKEM.NS",
        "AMBUJACEM.NS", "ANGELONE.NS", "APLAPOLLO.NS", "APOLLOTYRE.NS",
        "ASHOKLEY.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS",
        "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS",
        "BANKINDIA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS",
        "BHEL.NS", "BIOCON.NS", "BOSCHLTD.NS", "CANBK.NS", "CANFINHOME.NS",
        "CDSL.NS", "CESC.NS", "CGPOWER.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS",
        "CROMPTON.NS", "CUB.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS",
        "DEEPAKNTR.NS", "DELHIVERY.NS", "DELTACORP.NS", "DHANI.NS", "DMART.NS",
        "EASEMYTRIP.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS",
        "FINCABLES.NS", "FORTIS.NS", "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS",
        "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GUJGASLTD.NS",
        "HAL.NS", "HAVELLS.NS", "HDFCAMC.NS", "HINDCOPPER.NS", "HINDPETRO.NS",
        "HONAUT.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDEA.NS", "IDFC.NS",
        "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS",
        "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", "INTELLECT.NS",
        "IOC.NS", "IPCALAB.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS",
        "JKCEMENT.NS", "JSL.NS", "JUBLFOOD.NS", "KALYANKJIL.NS", "KOTAKBANK.NS",
        "LALPATHLAB.NS", "LAURUSLABS.NS", "LICHSGFIN.NS", "LODHA.NS",
        "LTF.NS", "LTIM.NS", "LUPIN.NS", "M&M.NS", "MANAPPURAM.NS",
        "MARICO.NS", "MAXHEALTH.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS",
        "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS",
        "NATIONALUM.NS", "NAUKRI.NS", "NAVINFLUOR.NS", "NMDC.NS", "NYKAA.NS",
        "OBEROIRLTY.NS", "OFSS.NS", "OIL.NS", "PAYTM.NS", "PEL.NS",
        "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS",
        "PNB.NS", "POLICYBZR.NS", "POLYCAB.NS", "POONAWALLA.NS", "POWERGRID.NS",
        "PRESTIGE.NS", "PVRINOX.NS", "RAIN.NS", "RAMCOCEM.NS", "RBLBANK.NS",
        "RECLTD.NS", "SAIL.NS", "SBICARD.NS", "SHREECEM.NS", "SIEMENS.NS",
        "SRF.NS", "STAR.NS", "SUNTV.NS", "SYNGENE.NS", "TATACHEM.NS",
        "TATACOMM.NS", "TATAELXSI.NS", "TATAPOWER.NS", "TORNTPHARM.NS",
        "TRENT.NS", "TVSMOTOR.NS", "UJJIVAN.NS", "ULTRACEMCO.NS", "UNIONBANK.NS",
        "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WHIRLPOOL.NS", "ZOMATO.NS",
        "ZYDUSLIFE.NS",
    ]
    # Remove duplicates
    return list(set(stocks))

# ===================== TECHNICAL INDICATORS =====================

def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(df, fast=12, slow=26, signal=9):
    exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line, macd_line - signal_line

def calculate_adx(df, period=14):
    high, low, close = df['High'], df['Low'], df['Close']
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
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
    return sma + (std * std_dev), sma - (std * std_dev)

def calculate_vwap(df):
    df = df.copy()
    df['Date'] = df.index.date
    vwap_values = []
    for date in df['Date'].unique():
        day_data = df[df['Date'] == date]
        tp = (day_data['High'] + day_data['Low'] + day_data['Close']) / 3
        cum_pv = (tp * day_data['Volume']).cumsum()
        cum_vol = day_data['Volume'].cumsum()
        vwap_values.extend((cum_pv / cum_vol).values)
    return pd.Series(vwap_values, index=df.index)

def calculate_ichimoku(df, tenkan=9, kijun=26, senkou_b=52):
    tenkan_sen = (df['High'].rolling(tenkan).max() + df['Low'].rolling(tenkan).min()) / 2
    kijun_sen = (df['High'].rolling(kijun).max() + df['Low'].rolling(kijun).min()) / 2
    senkou_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
    senkou_b_vals = (df['High'].rolling(senkou_b).max() + df['Low'].rolling(senkou_b).min()) / 2
    senkou_b_vals = senkou_b_vals.shift(26)
    return {
        'tenkan': tenkan_sen, 'kijun': kijun_sen,
        'cloud_a': senkou_a, 'cloud_b': senkou_b_vals,
        'cloud_green': senkou_a > senkou_b_vals
    }

@st.cache_data(ttl=120)
def fetch_stock_data(symbol):
    """Fetch and analyze stock data"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period='1mo', interval='5m')
        
        if df.empty or len(df) < 50:
            return None
        
        # Get info
        try:
            info = stock.info
            name = info.get('shortName', symbol.replace('.NS', ''))
            sector = info.get('sector', 'N/A')
        except:
            name = symbol.replace('.NS', '')
            sector = 'N/A'
        
        # Price
        price = df['Close'].iloc[-1]
        open_p = df['Open'].iloc[0]
        high = df['High'].max()
        low = df['Low'].min()
        change = ((price - open_p) / open_p) * 100
        
        # Volume
        vol = df['Volume'].iloc[-1]
        avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
        vol_ratio = vol / avg_vol if avg_vol > 0 else 0
        
        # === LIQUIDITY CHECK ===
        if vol < min_volume or vol_ratio < min_volume_ratio:
            return None
        
        # OI
        try:
            fut = yf.Ticker(symbol.replace('.NS', '') + 'FUT.NS')
            fut_info = fut.info
            oi = fut_info.get('openInterest', 0)
            prev_oi = fut_info.get('previousOpenInterest', oi)
            oi_change = ((oi - prev_oi) / prev_oi * 100) if prev_oi > 0 else 0
        except:
            oi = 0
            oi_change = 0
        
        # RSI
        rsi = calculate_rsi(df, rsi_period).iloc[-1]
        
        # MACD
        macd_l, sig_l, hist = calculate_macd(df, macd_fast, macd_slow, macd_signal)
        macd_bull = macd_l.iloc[-1] > sig_l.iloc[-1]
        
        # EMA
        ema = df['Close'].ewm(span=ema_period, adjust=False).mean().iloc[-1]
        ema_bull = price > ema
        
        # ADX
        adx_s, plus_di, minus_di = calculate_adx(df, adx_period)
        adx_val = adx_s.iloc[-1]
        adx_bull = plus_di.iloc[-1] > minus_di.iloc[-1]
        adx_strong = adx_val > adx_threshold
        
        # VWAP
        vwap_s = calculate_vwap(df)
        vwap = vwap_s.iloc[-1]
        vwap_bull = price > vwap
        
        # Supertrend
        st_bull = calculate_supertrend(df, st_period, st_multiplier).iloc[-1] == 1
        
        # Bollinger
        bb_u, bb_l = calculate_bollinger_bands(df, bb_period, bb_std)
        bb_pos = ((price - bb_l.iloc[-1]) / (bb_u.iloc[-1] - bb_l.iloc[-1])) * 100 if (bb_u.iloc[-1] - bb_l.iloc[-1]) > 0 else 50
        
        # Ichimoku
        ichi = calculate_ichimoku(df, ichi_conv, ichi_base, ichi_span)
        tk_cross = ichi['tenkan'].iloc[-1] > ichi['kijun'].iloc[-1] if not pd.isna(ichi['tenkan'].iloc[-1]) else False
        above_cloud = price > max(ichi['cloud_a'].iloc[-1], ichi['cloud_b'].iloc[-1]) if not pd.isna(ichi['cloud_a'].iloc[-1]) else False
        below_cloud = price < min(ichi['cloud_a'].iloc[-1], ichi['cloud_b'].iloc[-1]) if not pd.isna(ichi['cloud_a'].iloc[-1]) else False
        cloud_bull = ichi['cloud_green'].iloc[-1] if not pd.isna(ichi['cloud_green'].iloc[-1]) else False
        
        return {
            'symbol': symbol.replace('.NS', ''),
            'name': name,
            'sector': sector,
            'price': price, 'open': open_p, 'high': high, 'low': low,
            'change': change, 'volume': vol, 'vol_ratio': vol_ratio, 'oi': oi,
            'rsi': rsi, 'macd_bull': macd_bull,
            'ema': ema, 'ema_bull': ema_bull,
            'adx': adx_val, 'adx_bull': adx_bull, 'adx_strong': adx_strong,
            'vwap': vwap, 'vwap_bull': vwap_bull,
            'supertrend_bull': st_bull, 'bb_pos': bb_pos,
            'tk_cross': tk_cross, 'above_cloud': above_cloud,
            'below_cloud': below_cloud, 'cloud_bull': cloud_bull,
            'oi_change': oi_change,
        }
    except:
        return None

def calculate_score(d):
    """Score 0-12"""
    bull = 0
    bear = 0
    
    # RSI
    if 40 <= d['rsi'] <= 60 and d['change'] > 0: bull += 1
    if 40 <= d['rsi'] <= 60 and d['change'] < 0: bear += 1
    if d['rsi'] < 30: bull += 1
    if d['rsi'] > 70: bear += 1
    
    # MACD
    if d['macd_bull']: bull += 2
    else: bear += 2
    
    # EMA
    if d['ema_bull']: bull += 1
    else: bear += 1
    
    # ADX
    if d['adx_strong']:
        if d['adx_bull']: bull += 2
        else: bear += 2
    
    # VWAP
    if d['vwap_bull']: bull += 1
    else: bear += 1
    
    # Supertrend
    if d['supertrend_bull']: bull += 1
    else: bear += 1
    
    # Ichimoku
    if d['above_cloud'] and d['tk_cross'] and d['cloud_bull']: bull += 2
    elif d['below_cloud'] and not d['tk_cross']: bear += 2
    
    # Volume
    if d['vol_ratio'] > 1.5:
        if d['change'] > 0: bull += 1
        else: bear += 1
    
    # OI
    if d['oi_change'] > min_oi_change:
        if d['change'] > 0: bull += 2
        else: bear += 1
    
    # BB
    if d['bb_pos'] > 80: bull += 1
    elif d['bb_pos'] < 20: bear += 1
    
    return min(bull, 12), min(bear, 12)

def get_tags(d):
    """Generate indicator tags"""
    tags = []
    if d['rsi'] < 30: tags.append(('RSI Oversold', 'tag-bullish'))
    if d['rsi'] > 70: tags.append(('RSI Overbought', 'tag-bearish'))
    if d['macd_bull']: tags.append(('MACD Bull', 'tag-bullish'))
    else: tags.append(('MACD Bear', 'tag-bearish'))
    if d['ema_bull']: tags.append(('EMA Above', 'tag-bullish'))
    else: tags.append(('EMA Below', 'tag-bearish'))
    if d['adx_strong']: tags.append((f'ADX {d["adx"]:.0f}', 'tag-bullish' if d['adx_bull'] else 'tag-bearish'))
    if d['vwap_bull']: tags.append(('VWAP Above', 'tag-vwap'))
    else: tags.append(('VWAP Below', 'tag-bearish'))
    if d['supertrend_bull']: tags.append(('ST Buy', 'tag-bullish'))
    else: tags.append(('ST Sell', 'tag-bearish'))
    if d['above_cloud']: tags.append(('Above Cloud', 'tag-ichimoku'))
    if d['below_cloud']: tags.append(('Below Cloud', 'tag-ichimoku'))
    if d['tk_cross']: tags.append(('TK Cross', 'tag-ichimoku'))
    if abs(d['oi_change']) > min_oi_change:
        tags.append((f'OI {d["oi_change"]:+.1f}%', 'tag-oi'))
    return tags

# ===================== MAIN =====================

all_stocks = get_all_fno_stocks()
st.info(f"📊 Scanning **{len(all_stocks)}** NSE F&O stocks (Min Vol: {min_volume:,}, Min Vol Ratio: {min_volume_ratio}x)...")

if auto_refresh:
    time_module.sleep(refresh_interval)
    st.rerun()

results = []
progress = st.progress(0)
status = st.empty()

for i, sym in enumerate(all_stocks):
    if i % 5 == 0:
        status.text(f"Scanning... {i+1}/{len(all_stocks)} - {sym.replace('.NS', '')}")
    d = fetch_stock_data(sym)
    if d:
        bull_s, bear_s = calculate_score(d)
        d['bull_score'] = bull_s
        d['bear_score'] = bear_s
        d['net_score'] = bull_s - bear_s
        results.append(d)
    progress.progress((i+1) / len(all_stocks))

progress.empty()
status.empty()

if results:
    df = pd.DataFrame(results)
    
    # Summary
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Scanned", f"{len(df)}/{len(all_stocks)}")
    c2.metric("📈 Advancers", f"{len(df[df['change']>0])}")
    c3.metric("📉 Decliners", f"{len(df[df['change']<0])}")
    c4.metric("💎 Above VWAP", f"{len(df[df['vwap_bull']])}")
    
    st.markdown("---")
    
    # Top 10 Bullish
    df_bull = df[df['change'] > 0].nlargest(10, 'bull_score')
    
    st.markdown("## 🟢 Top 10 Bullish Stocks")
    st.markdown(f"*Filtered from {len(df)} liquid F&O stocks | RSI • MACD • EMA • ADX • VWAP • Ichimoku • Supertrend • BB • OI*")
    st.markdown("---")
    
    for _, r in df_bull.iterrows():
        tags = get_tags(r)
        tags_h = ' '.join([f'<span class="indicator-tag {t[1]}">{t[0]}</span>' for t in tags])
        sc = "score-high" if r['bull_score'] >= 9 else "score-medium"
        cd = "strong-bullish" if r['bull_score'] >= 9 else "moderate-bullish"
        sig = "🔥 STRONG" if r['bull_score'] >= 9 else "📈 BUY"
        
        st.markdown(f"""
            <div class="metric-card {cd}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <h3 style="margin:0;color:white;">{r['name']} <small style="color:#888;">({r['symbol']})</small></h3>
                        <span style="font-size:11px;color:#888;">{r['sector']} | Vol: {r['volume']/1e6:.2f}M | OI: {r['oi']/1e6:.2f}M</span>
                    </div>
                    <div class="score-badge {sc}">{sig} {r['bull_score']:.0f}/12</div>
                </div>
                <div style="margin:10px 0;display:flex;align-items:baseline;gap:15px;">
                    <span style="font-size:26px;font-weight:bold;">₹{r['price']:.2f}</span>
                    <span class="bullish-text" style="font-size:18px;">{r['change']:+.2f}%</span>
                </div>
                <div class="indicator-row">
                    <div class="indicator-item">
                        <div class="indicator-label">RSI</div>
                        <div class="indicator-value" style="color:{'#00C853' if 40<=r['rsi']<=60 else '#FF1744' if r['rsi']>70 else '#FFD700'};">{r['rsi']:.0f}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">MACD</div>
                        <div class="indicator-value" style="color:{'#00C853' if r['macd_bull'] else '#FF1744'};">{'Bull' if r['macd_bull'] else 'Bear'}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">EMA</div>
                        <div class="indicator-value" style="color:{'#00C853' if r['ema_bull'] else '#FF1744'};">{'Above' if r['ema_bull'] else 'Below'}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">VWAP</div>
                        <div class="indicator-value" style="color:{'#00FFFF' if r['vwap_bull'] else '#FF1744'};">{'Above' if r['vwap_bull'] else 'Below'}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">Cloud</div>
                        <div class="indicator-value" style="color:#FF69B4;">{'Above' if r['above_cloud'] else 'In/Below'}</div>
                    </div>
                </div>
                <div style="margin-top:8px;">{tags_h}</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Top 10 Bearish
    df_bear = df[df['change'] < 0].nlargest(10, 'bear_score')
    
    st.markdown("---")
    st.markdown("## 🔴 Top 10 Bearish Stocks")
    st.markdown(f"*Filtered from {len(df)} liquid F&O stocks | RSI • MACD • EMA • ADX • VWAP • Ichimoku • Supertrend • BB • OI*")
    st.markdown("---")
    
    for _, r in df_bear.iterrows():
        tags = get_tags(r)
        tags_h = ' '.join([f'<span class="indicator-tag {t[1]}">{t[0]}</span>' for t in tags])
        sc = "score-high" if r['bear_score'] >= 9 else "score-medium"
        cd = "strong-bearish" if r['bear_score'] >= 9 else "moderate-bearish"
        sig = "🔥 STRONG" if r['bear_score'] >= 9 else "📉 SELL"
        
        st.markdown(f"""
            <div class="metric-card {cd}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <h3 style="margin:0;color:white;">{r['name']} <small style="color:#888;">({r['symbol']})</small></h3>
                        <span style="font-size:11px;color:#888;">{r['sector']} | Vol: {r['volume']/1e6:.2f}M | OI: {r['oi']/1e6:.2f}M</span>
                    </div>
                    <div class="score-badge {sc}">{sig} {r['bear_score']:.0f}/12</div>
                </div>
                <div style="margin:10px 0;display:flex;align-items:baseline;gap:15px;">
                    <span style="font-size:26px;font-weight:bold;">₹{r['price']:.2f}</span>
                    <span class="bearish-text" style="font-size:18px;">{r['change']:+.2f}%</span>
                </div>
                <div class="indicator-row">
                    <div class="indicator-item">
                        <div class="indicator-label">RSI</div>
                        <div class="indicator-value" style="color:{'#FF1744' if 40<=r['rsi']<=60 else '#00C853' if r['rsi']<30 else '#FFD700'};">{r['rsi']:.0f}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">MACD</div>
                        <div class="indicator-value" style="color:{'#00C853' if r['macd_bull'] else '#FF1744'};">{'Bull' if r['macd_bull'] else 'Bear'}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">EMA</div>
                        <div class="indicator-value" style="color:{'#00C853' if r['ema_bull'] else '#FF1744'};">{'Above' if r['ema_bull'] else 'Below'}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">VWAP</div>
                        <div class="indicator-value" style="color:{'#00FFFF' if r['vwap_bull'] else '#FF1744'};">{'Above' if r['vwap_bull'] else 'Below'}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">Cloud</div>
                        <div class="indicator-value" style="color:#FF69B4;">{'Above' if r['above_cloud'] else 'In/Below'}</div>
                    </div>
                </div>
                <div style="margin-top:8px;">{tags_h}</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Downloads
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 All Results CSV", df.to_csv(index=False), f"fno_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
    with col2:
        st.download_button("📥 Bullish Picks CSV", df_bull.to_csv(index=False), f"bullish_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")

else:
    st.warning(f"⚠️ No stocks matched the filters. Try lowering Min Volume (currently {min_volume:,}) or Min Volume Ratio (currently {min_volume_ratio}x).")
    st.info("💡 Suggested settings for initial scan: Min Volume = 50,000, Min Volume Ratio = 0.5")

st.markdown("---")
st.caption("⚠️ Educational purposes only. Works anytime - Market open or closed.")
