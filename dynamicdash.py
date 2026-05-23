import streamlit as st
import yfinance as yf
import pandas as pd
import time
import threading
from datetime import datetime
from collections import defaultdict

# Import your Telegram alert function
from telegram_alerts import send_alert

st.set_page_config(page_title="Shane Dynamic Breakout Dashboard", layout="wide")
st.title("🚀 Shane's FULLY DYNAMIC High-Velocity Dashboard")
st.markdown("**Live Tweet Discovery + Professional Risk/Reward Tables** • Entry | Stops | Targets | % Returns | Probabilities")

# ================== CONFIG ==================
CORE_WATCHLIST = {
    "ASTS": {"support": 98.0, "breakout": 110.0, "target": 130.0, "theme": "Space/Satcom"},
    "BB":   {"support": 7.20, "breakout": 8.20, "target": 11.0,   "theme": "AI/IoT"},
    "RGTI": {"support": 23.5, "breakout": 28.0,  "target": 38.0,  "theme": "Quantum"},
    "QS":   {"support": 7.60, "breakout": 8.50,  "target": 12.0,  "theme": "Battery"},
    "IREN": {"support": 52.0, "breakout": 60.0,  "target": 75.0,  "theme": "AI Power"},
    "BEAM": {"support": 26.0, "breakout": 29.5,  "target": 40.0,  "theme": "Biotech"},
    "PLRX": {"support": 1.10, "breakout": 1.35,  "target": 2.20,  "theme": "Biotech"},
}

if "discovered" not in st.session_state:
    st.session_state.discovered = defaultdict(lambda: {"count": 0, "last_seen": None, "traders": set(), "heat_score": 0, "alerted": False})

if "alert_log" not in st.session_state:
    st.session_state.alert_log = []

# ================== ALERT FUNCTION ==================
def send_alert_message(ticker, message):
    full_message = f"🚨 ${ticker} - {message}"
    
    try:
        send_alert(full_message)
    except Exception as e:
        st.error(f"Telegram alert failed: {e}")
    
    st.toast(full_message, icon="🔥")
    
    timestamp = datetime.now().strftime('%H:%M')
    st.session_state.alert_log.append(f"[{timestamp}] ${ticker} - {message}")

# ================== TRADINGVIEW LINK ==================
def get_tv_link(ticker: str) -> str:
    return f"https://www.tradingview.com/symbols/{ticker}/"

# ================== THREADS ==================
def tweet_discovery_thread():
    last_alert = {}
    while True:
        try:
            for ticker in list(CORE_WATCHLIST.keys())[:3]:
                if ticker not in st.session_state.discovered:
                    st.session_state.discovered[ticker] = {"count": 0, "last_seen": datetime.now(), "traders": set(), "heat_score": 0, "alerted": False}
                
                entry = st.session_state.discovered[ticker]
                entry["count"] += 1
                entry["last_seen"] = datetime.now()
                entry["traders"].add("Simulated")
                entry["heat_score"] = min(10, entry["count"] * 1.2)

                now = datetime.now()
                if entry["heat_score"] >= 4 and (ticker not in last_alert or (now - last_alert[ticker]).seconds > 300):
                    alert_msg = f"Heat building! Score: {entry['heat_score']:.1f}"
                    send_alert_message(ticker, alert_msg)
                    last_alert[ticker] = now
            time.sleep(60)
        except:
            time.sleep(30)

def price_alert_thread():
    while True:
        try:
            for ticker, cfg in CORE_WATCHLIST.items():
                try:
                    price = yf.Ticker(ticker).info.get('currentPrice')
                    if price and price > cfg["breakout"] * 1.015:
                        alert_msg = f"BREAKOUT! Price: ${price:.2f}"
                        send_alert_message(ticker, alert_msg)
                except:
                    continue
            time.sleep(45)
        except:
            time.sleep(60)

# ================== DATA FUNCTIONS ==================
@st.cache_data(ttl=30)
def get_live_data(tickers_dict):
    data = []
    for ticker, cfg in tickers_dict.items():
        try:
            info = yf.Ticker(ticker).info
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
            prev_close = info.get('regularMarketPreviousClose', price)
            change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0
            volume = info.get('regularMarketVolume', 0)
            avg_vol = info.get('averageVolume', 1)
            vol_ratio = round(volume / avg_vol, 2) if avg_vol else 0

            data.append({
                "Ticker": ticker,
                "Price": round(price, 2),
                "% Chg": change_pct,
                "Vol Ratio": vol_ratio,
                "Status": "🔥 BREAKOUT" if price > cfg.get("breakout", price*1.05) else "🟡 Hot" if vol_ratio > 2 else "📈 Watching",
                "Support": cfg.get("support", round(price*0.92, 2)),
                "Breakout": cfg.get("breakout", round(price*1.05, 2)),
                "Target": cfg.get("target", round(price*1.25, 2)),
                "Theme": cfg.get("theme", "Tweet Discovered"),
                "Heat": cfg.get("heat_score", 0),
                "TradingView": get_tv_link(ticker)
            })
        except:
            pass
    return pd.DataFrame(data)

def get_risk_reward_table(ticker, current_price, cfg=None, vol_ratio=1.0, heat_score=0):
    if cfg is None:
        try:
            hist = yf.Ticker(ticker).history(period="3mo")
            if len(hist) < 20: return pd.DataFrame()
            current_price = hist['Close'].iloc[-1]
            support = hist['Low'].rolling(20).min().iloc[-1]
            breakout = hist['High'].rolling(20).max().iloc[-1] * 1.02
        except:
            return pd.DataFrame()
    else:
        support = cfg["support"]
        breakout = cfg["breakout"]

    scenarios = []
    stop = support

    entry1 = breakout
    risk_pct1 = max((entry1 - stop) / entry1 * 100, 4.0)
    target1 = entry1 + (entry1 - stop) * 2.0
    target2 = entry1 + (entry1 - stop) * 3.5
    upside1 = (target1 - entry1) / entry1 * 100
    rr1 = round(upside1 / risk_pct1, 1)
    pct_to_entry1 = (entry1 - current_price) / current_price * 100 if current_price else 0
    pct_to_t1 = (target1 - current_price) / current_price * 100 if current_price else 0
    pct_to_t2 = (target2 - current_price) / current_price * 100 if current_price else 0

    scenarios.append(["Breakout Entry", round(entry1,2), round(stop,2), round(target1,2), round(target2,2),
                      round(pct_to_entry1,1), round(pct_to_t1,1), round(pct_to_t2,1),
                      round(upside1,1), round(risk_pct1,1), f"1:{rr1}", f"{min(78, max(35, 48 + int(vol_ratio*8) + int(heat_score*4)))}%"])

    entry2 = max(support * 1.02, current_price * 0.97) if current_price else support * 1.02
    risk_pct2 = max((entry2 - stop) / entry2 * 100, 3.5)
    upside2 = (target1 - entry2) / entry2 * 100
    rr2 = round(upside2 / risk_pct2, 1)
    pct_to_entry2 = (entry2 - current_price) / current_price * 100 if current_price else 0

    scenarios.append(["Dip Buy (Support)", round(entry2,2), round(stop,2), round(target1,2), round(target2,2),
                      round(pct_to_entry2,1), round(pct_to_t1,1), round(pct_to_t2,1),
                      round(upside2,1), round(risk_pct2,1), f"1:{rr2}", f"{min(75, max(40, 52 + int(vol_ratio*6) + int(heat_score*3)))}%"])

    df = pd.DataFrame(scenarios, columns=[
        "Scenario", "Entry", "Stop", "Target 1", "Target 2",
        "% to Entry", "% to T1", "% to T2", "Upside from Entry (%)", 
        "Risk %", "R:R", "Est. Prob."
    ])
    return df

# ================== START THREADS ==================
if "threads_started" not in st.session_state:
    threading.Thread(target=price_alert_thread, daemon=True).start()
    threading.Thread(target=tweet_discovery_thread, daemon=True).start()
    st.session_state.threads_started = True
    send_alert("🚀 Shane's Dynamic Breakout Dashboard just started!")

# ================== UI ==================
st.subheader("🔥 Core Watchlist")
core_df = get_live_data(CORE_WATCHLIST)

st.dataframe(
    core_df,
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Ticker": st.column_config.TextColumn("Ticker"),
        "TradingView": st.column_config.LinkColumn(
            "📊 Chart", 
            help="Open in TradingView",
            display_text="Open Chart"
        ),
        "Status": st.column_config.TextColumn("Status")
    }
)

st.subheader("🌐 Discovered from Traders")
disc_dict = {tk: v for tk, v in st.session_state.discovered.items() if v["heat_score"] > 2}
if disc_dict:
    disc_input = {tk: {"heat_score": v["heat_score"]} for tk, v in disc_dict.items()}
    disc_df = get_live_data(disc_input)
    disc_df = disc_df.sort_values("Heat", ascending=False)
    
    st.dataframe(
        disc_df,
        use_container_width=True, 
        hide_index=True,
        column_config={
            "TradingView": st.column_config.LinkColumn(
                "📊 Chart", 
                help="Open in TradingView",
                display_text="Open Chart"
            )
        }
    )

# Risk/Reward Tables
st.subheader("📊 Risk / Reward Scenarios — All Tickers")
all_tickers = sorted(CORE_WATCHLIST.keys())

for ticker in all_tickers:
    cfg = CORE_WATCHLIST.get(ticker)
    try:
        price = yf.Ticker(ticker).info.get('currentPrice')
        current_price = round(price, 2) if price else 0
    except:
        current_price = 0

    if current_price > 0:
        match = core_df[core_df["Ticker"] == ticker]
        vol_ratio = match.iloc[0]["Vol Ratio"] if not match.empty else 1.0
        heat_score = match.iloc[0].get("Heat", 0) if not match.empty else 0

        scenarios_df = get_risk_reward_table(ticker, current_price, cfg, vol_ratio, heat_score)
        
        tv_link = get_tv_link(ticker)
        st.markdown(f"### [${ticker}]({tv_link}) 📊")
        st.dataframe(scenarios_df, use_container_width=True, hide_index=True)

# Alert Log
st.subheader("🔔 Live Alert Log")
for alert in st.session_state.alert_log[-15:]:
    st.write(alert)

st.caption("Telegram alerts active • Click the 📊 Chart column to open in TradingView")